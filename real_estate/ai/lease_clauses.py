"""AI lease clause generator (Feature L)."""
import frappe
from .claude_client import call_claude


@frappe.whitelist()
def generate_lease_clauses(lease_type: str, country: str = "", special_requirements: str = "") -> str:
    """
    Generate legally-aware lease clauses using Claude.
    Returns clause text suitable for the special_clauses field.
    """
    country_context = f"in {country}" if country else ""
    special = f"\nSpecial requirements from landlord: {special_requirements}" if special_requirements else ""

    system = (
        "You are an expert real estate lawyer specializing in residential and commercial tenancy law. "
        "Draft clear, professional lease clauses that protect both landlord and tenant. "
        "Use plain English. Do not include any preamble or sign-off — only the clause text."
    )

    prompt = f"""Draft special clauses for a {lease_type} lease agreement {country_context}.

Include clauses covering:
1. Subletting restrictions
2. Property alterations and modifications
3. Pet policy
4. Noise and nuisance
5. Insurance obligations
6. Utilities responsibility
7. Maintenance and repair obligations
8. Early termination conditions
9. Renewal terms
10. Access for inspections{special}

Format each clause with a bold heading and 2-3 sentences of content."""

    result = call_claude(prompt, max_tokens=2048, system=system)
    if not result:
        return "AI clause generation failed. Please configure the Claude API key and try again."
    return result
