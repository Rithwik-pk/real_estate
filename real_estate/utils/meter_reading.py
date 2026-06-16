"""
IoT-ready meter reading receiver.
Endpoint: POST /api/method/real_estate.utils.meter_reading.receive_meter_reading
"""
import frappe
from frappe.utils import nowdate, flt


@frappe.whitelist(allow_guest=False)
def receive_meter_reading(
    unit_name: str,
    utility_type: str,
    reading: float,
    reading_date: str = None,
):
    """
    Receive a meter reading from an IoT device or manual entry.
    Stores the reading and optionally updates an open Rent Invoice.
    """
    reading = flt(reading)
    reading_date = reading_date or nowdate()
    # Find the latest previous reading
    prev = frappe.db.sql(
        """
        SELECT uc.current_reading
        FROM `tabUtility Charge` uc
        JOIN `tabRent Invoice` ri ON uc.parent = ri.name
        WHERE ri.lease IN (
            SELECT name FROM `tabLease Agreement`
            WHERE property_unit = %s AND docstatus = 1
        )
        AND uc.utility_type = %s
        ORDER BY ri.billing_period_end DESC LIMIT 1
        """,
        (unit_name, utility_type),
    )
    previous_reading = flt(prev[0][0]) if prev else 0.0
    consumption = reading - previous_reading

    # Find active open Rent Invoice for this unit
    lease_name = frappe.db.get_value(
        "Property Unit", unit_name, "current_lease"
    )
    if lease_name:
        open_inv = frappe.db.get_value(
            "Rent Invoice",
            {"lease": lease_name, "status": "Unpaid", "docstatus": 0},
        )
        if open_inv:
            inv = frappe.get_doc("Rent Invoice", open_inv)
            existing_row = next(
                (r for r in inv.utility_charges if r.utility_type == utility_type), None
            )
            rate = _get_utility_rate(utility_type, unit_name, consumption)
            if existing_row:
                existing_row.current_reading = reading
                existing_row.previous_reading = previous_reading
                existing_row.consumption = consumption
                existing_row.rate_per_unit = rate
                existing_row.amount = consumption * rate
            else:
                inv.append("utility_charges", {
                    "utility_type": utility_type,
                    "previous_reading": previous_reading,
                    "current_reading": reading,
                    "consumption": consumption,
                    "rate_per_unit": rate,
                    "amount": consumption * rate,
                })
            inv.save(ignore_permissions=True)
            return {"status": "ok", "invoice": open_inv, "consumption": consumption}
    return {"status": "ok", "no_invoice": True, "consumption": consumption}


def _get_utility_rate(utility_type, unit_name, consumption):
    """Look up rate from Utility Rate Card."""
    unit = frappe.get_doc("Property Unit", unit_name)
    prop = frappe.get_doc("Property", unit.property)
    card = frappe.db.get_value(
        "Utility Rate Card",
        {
            "utility_type": utility_type,
            "is_active": 1,
            "city": ["in", [prop.city, ""]],
        },
        order_by="effective_from desc",
    )
    if card:
        rc = frappe.get_doc("Utility Rate Card", card)
        return rc.calculate_cost(consumption) / consumption if consumption else 0
    return 0
