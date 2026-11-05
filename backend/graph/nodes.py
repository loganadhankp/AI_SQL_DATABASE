"""
LangGraph Node Definitions for AI SQL Database Analyst.
Implements the 8 core agentic steps with self-healing feedback.
"""

import time
from typing import Dict, Any
from backend.graph.state import AgentState
from backend.agents.question_analyzer import analyze_question
from backend.tools.schema_inspector import SchemaInspector
from backend.agents.sql_generator import generate_sql
from backend.tools.sql_validator import SQLValidator
from backend.tools.database_executor import DatabaseExecutor
from backend.agents.result_analyzer import ResultAnalyzer


def question_understanding_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Analyzes user intent, extracts entities, and flags ambiguity."""
    t0 = time.perf_counter()
    tables = state.get("available_tables") or []
    if not tables and state.get("engine"):
        tables = SchemaInspector.get_table_names(state["engine"])

    analysis = analyze_question(state["user_question"], available_tables=tables)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "question_understanding",
        "status": "completed",
        "duration_ms": elapsed,
        "detail": f"Intent: {analysis.user_intent}. Tables: {', '.join(analysis.candidate_tables) or 'general'}",
    }

    if analysis.is_ambiguous:
        return {
            "candidate_tables": analysis.candidate_tables,
            "needs_clarification": True,
            "clarification_message": analysis.clarification_prompt or "Could you clarify your request?",
            "execution_steps": [step],
        }

    return {
        "candidate_tables": analysis.candidate_tables,
        "available_tables": tables,
        "needs_clarification": False,
        "execution_steps": [step],
    }


def schema_inspection_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Inspects relevant database tables, column types, and foreign keys."""
    t0 = time.perf_counter()
    engine = state["engine"]
    db_name = state["database_name"]

    # If the database has 15 or fewer tables, include all tables so the LLM has complete schema context.
    # Otherwise, filter to candidate tables to conserve prompt space in massive enterprise schemas.
    all_tables = state.get("available_tables") or []
    if not all_tables and engine:
        all_tables = SchemaInspector.get_table_names(engine)

    candidate = state.get("candidate_tables")
    relevant = candidate if len(all_tables) > 15 else None

    # Generate schema context for candidate tables (or full schema for standard DBs)
    schema_text = SchemaInspector.format_schema_for_llm(
        engine=engine,
        database_name=db_name,
        relevant_tables=relevant,
    )
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "schema_inspection",
        "status": "completed",
        "duration_ms": elapsed,
        "detail": f"Introspected schema relationships for database '{db_name}'.",
    }

    return {
        "schema_context": schema_text,
        "execution_steps": [step],
    }


def sql_generation_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Generates structured SQL using Gemini with dynamic schema & error context."""
    t0 = time.perf_counter()

    try:
        gen_result = generate_sql(
            question=state["user_question"],
            schema_context=state["schema_context"],
            dialect=state.get("dialect", "mysql"),
            error_feedback=state.get("error_message"),
            previous_sql=state.get("generated_sql"),
        )
        elapsed = round((time.perf_counter() - t0) * 1000, 1)

        step = {
            "node": "sql_generation",
            "status": "completed",
            "duration_ms": elapsed,
            "detail": f"Generated SQL query (Confidence: {gen_result.confidence_score * 100:.0f}%).",
        }

        if gen_result.needs_clarification:
            return {
                "generated_sql": None,
                "needs_clarification": True,
                "clarification_message": gen_result.clarification_question,
                "execution_steps": [step],
            }

        return {
            "generated_sql": gen_result.sql_query,
            "sql_explanation": gen_result.explanation,
            "error_message": None,  # Reset prior error on new generation
            "execution_steps": [step],
        }

    except Exception as e:
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        step = {
            "node": "sql_generation",
            "status": "failed",
            "duration_ms": elapsed,
            "detail": f"LLM Generation error: {str(e)}",
        }
        return {
            "generated_sql": None,
            "error_message": str(e),
            "execution_steps": [step],
        }


def sql_validation_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: AST-based SQL validation ensuring single read-only SELECT."""
    t0 = time.perf_counter()
    sql = state.get("generated_sql", "")

    is_valid, message, sanitized = SQLValidator.validate_sql(
        sql=sql, dialect=state.get("dialect", "mysql")
    )
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "sql_validation",
        "status": "completed" if is_valid else "rejected",
        "duration_ms": elapsed,
        "detail": message,
    }

    return {
        "is_valid": is_valid,
        "sanitized_sql": sanitized if is_valid else None,
        "validation_error": message if not is_valid else None,
        "execution_steps": [step],
    }


def database_execution_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Executes validated SQL on the database engine."""
    t0 = time.perf_counter()
    engine = state["engine"]
    query = state["sanitized_sql"]

    result = DatabaseExecutor.execute_query(engine=engine, sql_query=query)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "database_execution",
        "status": "completed" if result.success else "failed",
        "duration_ms": elapsed,
        "detail": f"Returned {result.row_count} rows in {result.execution_time_ms} ms."
        if result.success
        else f"Execution failed: {result.error_message}",
    }

    if result.success:
        return {
            "execution_result": result.model_dump(),
            "error_message": None,
            "execution_steps": [step],
        }
    else:
        return {
            "execution_result": result.model_dump(),
            "error_message": result.error_message,
            "error_category": result.error_category,
            "execution_steps": [step],
        }


def error_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Node 6: Analyzes failure and increments retry counter for self-healing."""
    t0 = time.perf_counter()
    new_retry = state.get("retry_count", 0) + 1
    err_msg = state.get("validation_error") or state.get("error_message") or "Unknown execution error"
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "error_analysis",
        "status": "completed",
        "duration_ms": elapsed,
        "detail": f"Attempt {new_retry} of {state.get('max_retries', 2)}: Preparing query correction for '{err_msg[:60]}...'",
    }

    return {
        "retry_count": new_retry,
        "error_message": err_msg,
        "execution_steps": [step],
    }


def result_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Node 7: Generates business observations and data visualization recommendation."""
    t0 = time.perf_counter()
    exec_res = state.get("execution_result") or {}
    columns = exec_res.get("columns") or []
    rows = exec_res.get("rows") or []
    exec_time = exec_res.get("execution_time_ms", 0.0)

    analysis = ResultAnalyzer.analyze_results(
        question=state["user_question"],
        sql_query=state.get("sanitized_sql", ""),
        columns=columns,
        rows=rows,
        execution_time_ms=exec_time,
    )
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    step = {
        "node": "result_analysis",
        "status": "completed",
        "duration_ms": elapsed,
        "detail": f"Suggested chart: {analysis.chart.chart_type.upper()}. Extracted {len(analysis.observations)} observations.",
    }

    return {
        "final_explanation": analysis.summary,
        "observations": analysis.observations,
        "suggested_chart": analysis.chart.model_dump(),
        "execution_steps": [step],
    }


def response_generation_node(state: AgentState) -> Dict[str, Any]:
    """Node 8: Finalizes response and sets terminal workflow status."""
    exec_res = state.get("execution_result") or {}

    if state.get("needs_clarification"):
        status = "clarification_needed"
        explanation = state.get("clarification_message") or "Could you please clarify your request?"
    elif exec_res.get("success"):
        status = "completed"
        explanation = state.get("final_explanation") or state.get("sql_explanation") or "Query executed successfully."
    else:
        status = "failed"
        explanation = (
            state.get("error_message")
            or state.get("validation_error")
            or "Query execution could not be completed."
        )

    step = {
        "node": "response_generation",
        "status": status,
        "duration_ms": 1.0,
        "detail": f"Workflow finished with status: {status.upper()}.",
    }

    return {
        "workflow_status": status,
        "final_explanation": explanation,
        "execution_steps": [step],
    }
