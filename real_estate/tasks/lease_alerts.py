"""Lease expiry alert scheduler — runs daily."""
import frappe
from frappe.utils import add_days, date_diff, getdate, nowdate


ALERT_DAYS = [60, 30, 15]


def run_lease_expiry_alerts():
    today = getdate(nowdate())
    active_leases = frappe.get_all(
        "Lease Agreement",
        filters={"lease_status": "Active", "docstatus": 1},
        fields=["name", "tenant", "property_unit", "lease_end_date", "monthly_rent"],
    )
    for lease in active_leases:
        days_remaining = date_diff(lease.lease_end_date, today)
        if days_remaining in ALERT_DAYS:
            _send_expiry_alert(lease, days_remaining)
        if days_remaining <= 0:
            _mark_expired(lease)


def _send_expiry_alert(lease, days_remaining):
    tenant_email = frappe.db.get_value("Customer", lease.tenant, "email_id")
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Property Manager", "parenttype": "User"},
        pluck="parent",
    )
    recipients = managers
    if tenant_email:
        recipients.append(tenant_email)
    frappe.sendmail(
        recipients=recipients,
        subject=f"Lease Expiry Alert — {lease.name} expires in {days_remaining} days",
        message=f"""
            <p>Lease <strong>{lease.name}</strong> for unit <strong>{lease.property_unit}</strong>
            will expire in <strong>{days_remaining} days</strong>.</p>
            <p>Tenant: {lease.tenant}</p>
            <p>Monthly Rent: {lease.monthly_rent}</p>
            <p>Please contact the tenant to arrange renewal or move-out.</p>
        """,
        now=True,
    )


def _mark_expired(lease):
    frappe.db.set_value("Lease Agreement", lease.name, "lease_status", "Expired")
    frappe.db.set_value("Property Unit", lease.property_unit, {"status": "Available", "current_lease": None})
    frappe.db.commit()
