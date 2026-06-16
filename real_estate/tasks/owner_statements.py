"""Monthly owner statement auto-generation."""
import frappe
from frappe.utils import get_first_day, get_last_day, add_months, nowdate, getdate


def generate_owner_statements():
    """Create draft Owner Statements for all active properties at month end."""
    last_month_start = get_first_day(add_months(nowdate(), -1))
    properties = frappe.get_all(
        "Property",
        filters={"status": ("!=", "Under Maintenance")},
        fields=["name", "owner_link"],
    )
    for prop in properties:
        if not prop.owner_link:
            continue
        existing = frappe.db.exists(
            "Owner Statement",
            {"property": prop.name, "statement_month": last_month_start},
        )
        if existing:
            continue
        stmt = frappe.new_doc("Owner Statement")
        stmt.owner = prop.owner_link
        stmt.property = prop.name
        stmt.statement_month = last_month_start
        stmt.status = "Draft"
        stmt.flags.ignore_permissions = True
        stmt.insert()
    frappe.db.commit()
