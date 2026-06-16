"""AI owner statement narrative generator (Feature O)."""
import frappe
from .claude_client import call_claude


def generate_owner_narrative(statement_doc) -> str:
    """
    Write a 2-paragraph natural language summary of the Owner Statement.
    Called on Owner Statement submit.
    """
    system = (
        "You are a professional property management reporting assistant. "
        "Write clear, concise, positive-but-honest property portfolio narratives "
        "for property owners. Use formal but accessible language."
    )

    prompt = f"""Write a 2-paragraph Portfolio Highlights narrative for the following monthly owner statement.

Owner: {statement_doc.owner}
Property: {statement_doc.property}
Month: {statement_doc.statement_month}

Financial Summary:
- Gross Rent Collected: {statement_doc.gross_rent_collected}
- Maintenance Costs: {statement_doc.maintenance_costs}
- Management Fee ({statement_doc.management_fee_percent}%): {statement_doc.management_fee_amount}
- Net Payout: {statement_doc.net_payout}

Paragraph 1: Summarize income performance for the month.
Paragraph 2: Note maintenance activity and outlook for next month.
Keep it under 150 words total. Professional tone, no bullet points."""

    result = call_claude(prompt, max_tokens=400, system=system)
    return result or ""
