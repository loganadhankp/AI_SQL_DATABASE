"""
Question Understanding Agent Node.
Analyzes user requests, determines analytical intent, matches candidate tables,
and flags ambiguity or out-of-scope inquiries.
"""

import json
from typing import List, Optional
from google import genai
from google.genai import types
from backend.config import get_settings
from backend.schemas.query_generation import QuestionAnalysis

settings = get_settings()


def analyze_question(
    question: str,
    available_tables: List[str],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> QuestionAnalysis:
    """
    Analyzes user question to determine intent and identify candidate tables.
    Uses Gemini LLM when API key is provided, with deterministic fallback for tests.
    """
    active_key = api_key or settings.GEMINI_API_KEY
    active_model = model or settings.GEMINI_MODEL

    # Deterministic fallback if API key is not yet configured
    if not active_key or active_key.strip() in ("", "your_gemini_api_key_here"):
        return _fallback_analyze(question, available_tables)

    client = genai.Client(api_key=active_key)
    tables_str = ", ".join(f"`{t}`" for t in available_tables)

    prompt = f"""You are an expert Data Analyst assistant specializing in SQL database understanding.
Your task is to analyze the user's natural language question and match it against the accessible database tables.

Available Database Tables: {tables_str}
User Question: "{question}"

Analyze the question carefully:
1. Determine the user's analytical intent (e.g. 'ranking', 'aggregation', 'comparison', 'filtering', 'temporal_trend').
2. Identify mentioned entities (e.g., customers, products, revenue, cities, orders).
3. Identify which candidate tables from the available list are required.
4. If the question is completely irrelevant to relational data or impossible to formulate with the available tables, set is_ambiguous = True and provide a helpful clarification_prompt.
"""

    models_to_try = []
    if model:
        models_to_try.append(model)
    elif active_model:
        models_to_try.append(active_model)

    for fallback in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None
    for attempt_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=attempt_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuestionAnalysis,
                    temperature=0.0,
                ),
            )

            return QuestionAnalysis.model_validate_json(response.text)
        except Exception as e:
            last_error = e
            continue

    # Graceful fallback on API rate limit or network issue across models
    fallback = _fallback_analyze(question, available_tables)
    fallback.user_intent = f"heuristic_fallback ({type(last_error).__name__ if last_error else 'Unknown'})"
    return fallback


def _fallback_analyze(question: str, available_tables: List[str]) -> QuestionAnalysis:
    """Heuristic rule-based fallback when offline or during test mocking."""
    q_lower = question.lower()
    matched_tables = [t for t in available_tables if t.lower() in q_lower or t.lower()[:-1] in q_lower]

    # Keyword intent matching (temporal trend prioritized before general aggregation)
    intent = "general_query"
    if any(k in q_lower for k in ["top", "highest", "most", "best", "lowest"]):
        intent = "top_ranking"
    elif any(k in q_lower for k in ["monthly", "daily", "yearly", "last month", "this year", "trend"]):
        intent = "temporal_trend"
    elif any(k in q_lower for k in ["compare", "versus", "vs", "between"]):
        intent = "comparison"
    elif any(k in q_lower for k in ["total", "sum", "average", "count", "revenue", "sales"]):
        intent = "aggregation"

    return QuestionAnalysis(
        user_intent=intent,
        identified_entities=[w for w in ["customer", "product", "order", "payment", "city", "revenue"] if w in q_lower],
        candidate_tables=matched_tables or available_tables[:2],
        is_ambiguous=len(question.strip()) < 5,
        clarification_prompt="Could you provide more specific details?" if len(question.strip()) < 5 else None,
    )
