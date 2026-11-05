"""
Pydantic schemas for Question Understanding and SQL Generation.
Defines the structured output contracts for Google Gemini LLM.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionAnalysis(BaseModel):
    """Output from the Question Understanding Node."""
    user_intent: str = Field(description="Core analytical intent (e.g., 'top_ranking', 'revenue_aggregation', 'trend_analysis')")
    identified_entities: List[str] = Field(default_factory=list, description="Entities mentioned (e.g., 'customers', 'products', 'orders')")
    candidate_tables: List[str] = Field(default_factory=list, description="Tables likely required to answer the question")
    is_ambiguous: bool = Field(default=False, description="Whether the question lacks critical information to formulate a query")
    clarification_prompt: Optional[str] = Field(default=None, description="Clarifying question if ambiguous or unanswerable")


class SQLGenerationResult(BaseModel):
    """Output from the SQL Generation Node."""
    sql_query: str = Field(description="The executable read-only SQL query without markdown code fences or backticks")
    explanation: str = Field(description="Concise business-level explanation of how the query computes the result")
    relevant_tables: List[str] = Field(default_factory=list, description="List of tables referenced in the query")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    needs_clarification: bool = Field(default=False, description="True if clarification is required before execution")
    clarification_question: Optional[str] = Field(default=None, description="Question to ask the user if clarification is needed")
