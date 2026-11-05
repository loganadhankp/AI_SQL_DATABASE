"""
LangGraph Workflow Definition for AI SQL Database Analyst.
Assembles the 8 agent nodes and sets up conditional routing with self-healing retry loops.
"""

from langgraph.graph import StateGraph, END
from backend.graph.state import AgentState
from backend.graph.nodes import (
    question_understanding_node,
    schema_inspection_node,
    sql_generation_node,
    sql_validation_node,
    database_execution_node,
    error_analysis_node,
    result_analysis_node,
    response_generation_node,
)


# ------------------------------------------------------------------------------
# Conditional Edge Routers
# ------------------------------------------------------------------------------

def route_after_understanding(state: AgentState) -> str:
    """Routes to clarification response or proceeds to schema inspection."""
    if state.get("needs_clarification"):
        return "response_generation"
    return "schema_inspection"


def route_after_sql_generation(state: AgentState) -> str:
    """Routes to validation, or directly to response if generation flagged clarification/error."""
    if state.get("needs_clarification") or not state.get("generated_sql"):
        return "response_generation"
    return "sql_validation"


def route_after_validation(state: AgentState) -> str:
    """Routes to execution if safe; otherwise to error self-healing loop or aborts."""
    if state.get("is_valid"):
        return "database_execution"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count < max_retries:
        return "error_analysis"
    return "response_generation"


def route_after_execution(state: AgentState) -> str:
    """Routes to result analysis if successful; otherwise retries via error_analysis."""
    exec_result = state.get("execution_result") or {}
    if exec_result.get("success"):
        return "result_analysis"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count < max_retries:
        return "error_analysis"
    return "response_generation"


# ------------------------------------------------------------------------------
# Workflow Graph Construction
# ------------------------------------------------------------------------------

def create_analyst_workflow() -> StateGraph:
    """Builds and compiles the complete LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("question_understanding", question_understanding_node)
    workflow.add_node("schema_inspection", schema_inspection_node)
    workflow.add_node("sql_generation", sql_generation_node)
    workflow.add_node("sql_validation", sql_validation_node)
    workflow.add_node("database_execution", database_execution_node)
    workflow.add_node("error_analysis", error_analysis_node)
    workflow.add_node("result_analysis", result_analysis_node)
    workflow.add_node("response_generation", response_generation_node)

    # 2. Set Entrypoint
    workflow.set_entry_point("question_understanding")

    # 3. Add Edges & Conditional Routing
    workflow.add_conditional_edges(
        "question_understanding",
        route_after_understanding,
        {
            "schema_inspection": "schema_inspection",
            "response_generation": "response_generation",
        },
    )

    workflow.add_edge("schema_inspection", "sql_generation")

    workflow.add_conditional_edges(
        "sql_generation",
        route_after_sql_generation,
        {
            "sql_validation": "sql_validation",
            "response_generation": "response_generation",
        },
    )

    workflow.add_conditional_edges(
        "sql_validation",
        route_after_validation,
        {
            "database_execution": "database_execution",
            "error_analysis": "error_analysis",
            "response_generation": "response_generation",
        },
    )

    workflow.add_conditional_edges(
        "database_execution",
        route_after_execution,
        {
            "result_analysis": "result_analysis",
            "error_analysis": "error_analysis",
            "response_generation": "response_generation",
        },
    )

    # Self-healing retry loop: error_analysis routes back to sql_generation
    workflow.add_edge("error_analysis", "sql_generation")

    workflow.add_edge("result_analysis", "response_generation")
    workflow.add_edge("response_generation", END)

    return workflow.compile()


# Singleton compiled graph instance (lazy loaded)
_analyst_graph = None


def get_analyst_graph():
    """Lazily compiles and returns the singleton LangGraph workflow."""
    global _analyst_graph
    if _analyst_graph is None:
        _analyst_graph = create_analyst_workflow()
    return _analyst_graph


# For backwards-compatibility
class _LazyGraphProxy:
    def invoke(self, *args, **kwargs):
        return get_analyst_graph().invoke(*args, **kwargs)


analyst_graph = _LazyGraphProxy()
