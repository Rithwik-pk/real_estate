"""
Natural language portfolio analytics (Feature N).
Whitelisted endpoint called from the Frappe Desk widget.
"""
import frappe
from frappe.utils import nowdate, add_days, get_first_day, get_last_day
from .claude_client import call_claude


@frappe.whitelist()
def ask_portfolio(question: str) -> str:
    """
    Build portfolio context from live DB, send to Claude, return answer.
    """
    context = _build_portfolio_context()
    system = (
        "You are an intelligent real estate portfolio assistant. "
        "Answer questions about properties, tenants, rent collection, and maintenance "
        "based on the provided portfolio data. Be concise, use bullet points where helpful. "
        "If data is insufficient, say so."
    )
    prompt = f"""Portfolio Data (as of {nowdate()}):

{context}

User Question: {question}"""

    result = call_claude(prompt, max_tokens=800, system=system)
    return result or "Unable to process query. Please check AI configuration."


def _build_portfolio_context() -> str:
    today = nowdate()
    # Occupancy
    total_units = frappe.db.count("Property Unit")
    occupied = frappe.db.count("Property Unit", {"status": "Occupied"})
    available = frappe.db.count("Property Unit", {"status": "Available"})
    occupancy_rate = (occupied / total_units * 100) if total_units else 0

    # Rent collection this month
    month_start = get_first_day(today)
    month_end = get_last_day(today)
    paid = frappe.db.sql(
        "SELECT IFNULL(SUM(total_amount),0) FROM `tabRent Invoice` "
        "WHERE status='Paid' AND billing_period_start>=%s AND billing_period_start<=%s AND docstatus=1",
        (month_start, month_end),
    )[0][0]
    overdue = frappe.db.count("Rent Invoice", {"status": "Overdue", "docstatus": ("!=", 2)})

    # Expiring leases (next 60 days)
    exp_soon = frappe.get_all(
        "Lease Agreement",
        filters={
            "lease_status": "Active",
            "lease_end_date": ("between", [today, add_days(today, 60)]),
        },
        fields=["name", "property_unit", "tenant", "lease_end_date"],
        limit=10,
    )
    exp_text = "\n".join(
        f"  - {l.name}: unit {l.property_unit}, tenant {l.tenant}, expires {l.lease_end_date}"
        for l in exp_soon
    ) or "  None in next 60 days"

    # Open maintenance
    open_maint = frappe.db.count("Maintenance Request", {"status": ("in", ["Open", "Assigned", "In Progress"])})
    emergency_maint = frappe.db.count("Maintenance Request", {"status": "Open", "priority": "Emergency"})

    # Vacant > 30 days
    long_vacant = frappe.db.sql(
        """SELECT name, unit_number FROM `tabProperty Unit`
        WHERE status='Available'
        AND modified < DATE_SUB(NOW(), INTERVAL 30 DAY)""",
        as_dict=True,
    )
    vacant_text = "\n".join(f"  - {u.name} ({u.unit_number})" for u in long_vacant) or "  None"

    return f"""
Occupancy: {occupied}/{total_units} units occupied ({occupancy_rate:.1f}%)
Available Units: {available}

Rent Collection (this month):
  Paid: {paid}
  Overdue invoices: {overdue}

Expiring Leases (next 60 days):
{exp_text}

Maintenance:
  Open/Assigned/In Progress: {open_maint}
  Emergency: {emergency_maint}

Units Vacant >30 days:
{vacant_text}
"""
