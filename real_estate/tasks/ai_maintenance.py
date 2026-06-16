"""Weekly predictive maintenance using Claude AI."""
import frappe
from frappe.utils import nowdate, add_days


def run_predictive_maintenance():
    """Weekly job: for each unit, gather history and ask Claude to predict next failure."""
    units = frappe.get_all("Property Unit", filters={"status": "Occupied"}, pluck="name")
    for unit in units:
        try:
            _predict_for_unit(unit)
        except Exception as e:
            frappe.log_error(f"Predictive maintenance failed for {unit}: {e}", "AI Maintenance")


def _predict_for_unit(unit_name):
    history = frappe.get_all(
        "Maintenance Request",
        filters={"property_unit": unit_name, "status": "Completed"},
        fields=["category", "completion_date", "actual_cost"],
        order_by="completion_date desc",
        limit=20,
    )
    if len(history) < 3:
        return

    from real_estate.ai.claude_client import call_claude

    history_text = "\n".join(
        f"- {r.category} completed on {r.completion_date} (cost: {r.actual_cost or 0})"
        for r in history
    )
    prompt = f"""You are a property maintenance AI assistant.
Based on the maintenance history below for unit {unit_name}, predict:
1. The most likely next maintenance category needed
2. Suggested service date (relative to today: {nowdate()})
3. Recommended priority (Low/Medium/High)
4. Brief reasoning

Maintenance history:
{history_text}

Respond in JSON format:
{{"category": "...", "suggested_date": "YYYY-MM-DD", "priority": "...", "reasoning": "..."}}"""

    result = call_claude(prompt, max_tokens=300)
    if not result:
        return
    try:
        import json
        data = json.loads(result)
        req = frappe.new_doc("Maintenance Request")
        req.property_unit = unit_name
        req.category = data.get("category", "Other")
        req.priority = data.get("priority", "Low")
        req.reported_date = data.get("suggested_date", nowdate())
        req.description = f"[AI Prediction] {data.get('reasoning', 'Predictive maintenance suggested by AI.')}"
        req.status = "Open"
        req.flags.ignore_permissions = True
        req.insert()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Predictive maintenance parse error for {unit_name}: {e}", "AI Maintenance")
