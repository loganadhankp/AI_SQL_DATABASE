"""
Result Analysis & Data Visualization Suggestion Engine.
Analyzes query results to generate concise business insights, trends,
and determine the most suitable visualization (Bar, Line, Pie, or Table).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChartSuggestion(BaseModel):
    """Recommended visualization format for the result set."""
    chart_type: str = Field(default="none", description="'bar', 'line', 'pie', or 'none'")
    title: str = Field(default="", description="Suggested title for the chart")
    x_axis_key: Optional[str] = Field(default=None, description="Column key for X-axis / labels")
    y_axis_keys: List[str] = Field(default_factory=list, description="Column keys for Y-axis / numeric values")
    explanation: Optional[str] = None


class AnalysisResult(BaseModel):
    """Final business observations and chart recommendations."""
    summary: str = Field(description="Direct, concise answer to the user's question")
    observations: List[str] = Field(default_factory=list, description="Key data observations, comparisons, or totals")
    chart: ChartSuggestion = Field(default_factory=ChartSuggestion)


class ResultAnalyzer:
    """Deterministic & LLM-assisted data analyzer."""

    @classmethod
    def analyze_results(
        cls,
        question: str,
        sql_query: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        execution_time_ms: float,
    ) -> AnalysisResult:
        """
        Produces concise, factual observations based purely on returned rows.
        Does not hallucinate values not present in the data.
        """
        row_count = len(rows)

        # Handle empty results
        if row_count == 0:
            return AnalysisResult(
                summary="The query executed successfully, but returned 0 matching records.",
                observations=[
                    "No data matched the filter criteria in the database.",
                    "Verify if the specified date range, customer, or entity exists.",
                ],
                chart=ChartSuggestion(chart_type="none", title="No Data Available"),
            )

        # Handle single scalar result (e.g. SELECT COUNT(*) or SELECT SUM(...))
        if row_count == 1 and len(columns) == 1:
            col = columns[0]
            val = rows[0][col]
            formatted_val = f"${val:,.2f}" if isinstance(val, (int, float)) and "revenue" in col.lower() else f"{val:,}" if isinstance(val, int) else str(val)
            return AnalysisResult(
                summary=f"The calculated {col.replace('_', ' ')} is {formatted_val}.",
                observations=[f"Single aggregated value returned: {formatted_val} across the requested scope."],
                chart=ChartSuggestion(chart_type="none", title=col),
            )

        # Determine suitable chart visualization
        chart_suggestion = cls._determine_chart(columns, rows, question)

        # Generate factual observations
        observations = cls._generate_observations(columns, rows)

        summary = f"Retrieved {row_count} records in {execution_time_ms} ms answering: '{question}'."

        return AnalysisResult(
            summary=summary,
            observations=observations,
            chart=chart_suggestion,
        )

    @classmethod
    def _determine_chart(
        cls,
        columns: List[str],
        rows: List[Dict[str, Any]],
        question: str,
    ) -> ChartSuggestion:
        """Determines best chart type based on column types and cardinalities."""
        if len(columns) < 2 or len(rows) <= 1:
            return ChartSuggestion(chart_type="none", title="Table View")

        # Classify columns as numeric, date, or text
        numeric_cols = []
        date_cols = []
        text_cols = []

        sample_row = rows[0]
        for col in columns:
            val = sample_row.get(col)
            if isinstance(val, (int, float)) and not col.lower().endswith(("_id", "id")):
                numeric_cols.append(col)
            elif any(d in col.lower() for d in ["date", "month", "year", "day", "time"]):
                date_cols.append(col)
            else:
                text_cols.append(col)

        # If no numeric column to plot, use table
        if not numeric_cols:
            return ChartSuggestion(chart_type="none", title="Table View")

        y_col = numeric_cols[0]

        # 1. Line chart for temporal data (dates/months/years on X-axis)
        if date_cols and len(rows) >= 3:
            return ChartSuggestion(
                chart_type="line",
                title=f"Trend of {y_col.replace('_', ' ').title()} Over Time",
                x_axis_key=date_cols[0],
                y_axis_keys=[y_col],
                explanation="Time series trend visualization",
            )

        # 2. Pie chart for category distribution (small category count: 2 to 7)
        if text_cols and 2 <= len(rows) <= 7:
            # Check if values represent a distribution / breakdown
            x_col = text_cols[0]
            return ChartSuggestion(
                chart_type="pie",
                title=f"Breakdown of {y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                x_axis_key=x_col,
                y_axis_keys=[y_col],
                explanation="Category distribution",
            )

        # 3. Bar chart for categorical comparisons (up to 20 rows)
        if text_cols and len(rows) <= 25:
            x_col = text_cols[0]
            return ChartSuggestion(
                chart_type="bar",
                title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                x_axis_key=x_col,
                y_axis_keys=[y_col],
                explanation="Categorical comparison",
            )

        return ChartSuggestion(chart_type="none", title="Tabular View")

    @classmethod
    def _generate_observations(
        cls,
        columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> List[str]:
        """Calculates factual statistical observations from the result rows."""
        observations = []
        numeric_cols = [
            c for c in columns
            if rows and isinstance(rows[0].get(c), (int, float)) and not c.lower().endswith(("_id", "id"))
        ]

        if numeric_cols and len(rows) > 1:
            primary_metric = numeric_cols[0]
            values = [r[primary_metric] for r in rows if isinstance(r.get(primary_metric), (int, float))]

            if values:
                total_val = sum(values)
                avg_val = total_val / len(values)
                max_val = max(values)
                min_val = min(values)

                # Format as currency if metric name hints at money
                is_money = any(m in primary_metric.lower() for m in ["revenue", "price", "amount", "total", "sales", "spent"])
                fmt = (lambda v: f"${v:,.2f}") if is_money else (lambda v: f"{v:,.1f}" if isinstance(v, float) else f"{v:,}")

                observations.append(
                    f"Highest {primary_metric.replace('_', ' ')}: {fmt(max_val)}, Lowest: {fmt(min_val)}."
                )
                observations.append(
                    f"Total {primary_metric.replace('_', ' ')} across returned items: {fmt(total_val)} (Average: {fmt(avg_val)})."
                )

        if len(rows) > 0 and not observations:
            observations.append(f"Successfully returned {len(rows)} data records matching your question criteria.")

        return observations
