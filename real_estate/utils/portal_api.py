"""
Whitelisted API methods for the tenant self-service portal.
Called via /api/method/real_estate.utils.portal_api.*
"""
import frappe
from frappe import _
from frappe.utils import nowdate


def _get_tenant_customer():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."), frappe.AuthenticationError)
    return frappe.db.get_value("Customer", {"email_id": frappe.session.user})


@frappe.whitelist()
def submit_maintenance_request(unit_name, category, priority, description):
    tenant = _get_tenant_customer()
    if not tenant:
        frappe.throw(_("Your account is not linked to a tenant profile."))
    req = frappe.new_doc("Maintenance Request")
    req.property_unit = unit_name
    req.tenant = tenant
    req.category = category
    req.priority = priority
    req.description = description
    req.reported_date = nowdate()
    req.status = "Open"
    req.flags.ignore_permissions = True
    req.insert()
    frappe.db.commit()
    return req.name


@frappe.whitelist()
def get_invoice_pdf(invoice_name):
    tenant = _get_tenant_customer()
    if not tenant:
        frappe.throw(_("Login required."))
    inv_tenant = frappe.db.get_value("Rent Invoice", invoice_name, "tenant")
    if inv_tenant != tenant:
        frappe.throw(_("Access denied."))
    return frappe.get_print("Rent Invoice", invoice_name, as_pdf=True)


@frappe.whitelist()
def get_portal_data():
    """Return all portal data as JSON for SPA-style refresh."""
    tenant = _get_tenant_customer()
    if not tenant:
        return {"error": "not_linked"}
    from real_estate.www.tenant_portal.index import (
        _get_active_leases, _get_invoices, _get_maintenance_requests
    )
    return {
        "leases": _get_active_leases(tenant),
        "invoices": _get_invoices(tenant),
        "maintenance_requests": _get_maintenance_requests(tenant),
    }
