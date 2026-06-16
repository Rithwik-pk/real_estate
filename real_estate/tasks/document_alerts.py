"""Document expiry alerts — runs daily across all document vaults."""
import frappe
from frappe.utils import date_diff, getdate, nowdate


DOCUMENT_TABLES = {
    "Property": "Property",
    "Property Unit": "Property Unit",
    "Lease Agreement": "Lease Agreement",
    "Agent": "Agent",
}


def run_document_expiry_alerts():
    today = getdate(nowdate())
    for doctype in DOCUMENT_TABLES:
        docs = frappe.get_all(doctype, pluck="name")
        for doc_name in docs:
            try:
                doc = frappe.get_doc(doctype, doc_name)
                if not hasattr(doc, "documents"):
                    continue
                for row in doc.documents:
                    if not row.expiry_date:
                        continue
                    days_to_expiry = date_diff(row.expiry_date, today)
                    reminder_days = row.reminder_days or 30
                    if days_to_expiry <= reminder_days:
                        _send_document_alert(doctype, doc_name, row, days_to_expiry)
            except Exception as e:
                frappe.log_error(f"Doc expiry alert error: {e}", "Document Alerts")


def _send_document_alert(doctype, doc_name, row, days_to_expiry):
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Property Manager", "parenttype": "User"},
        pluck="parent",
    )
    if not managers:
        return
    urgency = "URGENT — EXPIRED" if days_to_expiry < 0 else f"expiring in {days_to_expiry} days"
    frappe.sendmail(
        recipients=managers,
        subject=f"Document Expiry Alert — {row.doc_type} on {doctype} {doc_name}",
        message=f"""
            <p>Document <strong>{row.doc_type}</strong> on <strong>{doctype}: {doc_name}</strong>
            is <strong>{urgency}</strong>.</p>
            <p>Expiry Date: {row.expiry_date}</p>
            <p>Please renew or replace this document immediately.</p>
        """,
        now=True,
    )
