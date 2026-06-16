"""Post-migrate setup tasks."""
import frappe


def after_migrate():
    _create_roles()
    _create_property_item()
    _create_tenant_custom_fields()


def _create_roles():
    for role in ["Property Manager", "Real Estate Agent", "Tenant", "Property Owner"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
    frappe.db.commit()


def _create_tenant_custom_fields():
    """Create tenant KYC/identity fields on the Customer DocType."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    custom_fields = {
        "Customer": [
            {
                "fieldname": "tenant_details_section",
                "fieldtype": "Section Break",
                "label": "Tenant Details",
                "insert_after": "customer_details",
                "collapsible": 1,
            },
            {"fieldname": "id_type", "fieldtype": "Select", "label": "ID Type",
             "options": "National ID\nPassport\nIqama", "insert_after": "tenant_details_section"},
            {"fieldname": "id_number", "fieldtype": "Data", "label": "ID Number", "insert_after": "id_type"},
            {"fieldname": "id_expiry", "fieldtype": "Date", "label": "ID Expiry Date", "insert_after": "id_number"},
            {"fieldname": "tenant_col_break", "fieldtype": "Column Break", "insert_after": "id_expiry"},
            {"fieldname": "nationality", "fieldtype": "Data", "label": "Nationality", "insert_after": "tenant_col_break"},
            {"fieldname": "employer", "fieldtype": "Data", "label": "Employer", "insert_after": "nationality"},
            {"fieldname": "monthly_income", "fieldtype": "Currency", "label": "Monthly Income", "insert_after": "employer"},
            {
                "fieldname": "emergency_section",
                "fieldtype": "Section Break",
                "label": "Emergency Contact",
                "insert_after": "monthly_income",
                "collapsible": 1,
            },
            {"fieldname": "emergency_contact_name", "fieldtype": "Data", "label": "Emergency Contact Name",
             "insert_after": "emergency_section"},
            {"fieldname": "emergency_contact_phone", "fieldtype": "Phone", "label": "Emergency Contact Phone",
             "insert_after": "emergency_contact_name"},
            {
                "fieldname": "kyc_section",
                "fieldtype": "Section Break",
                "label": "KYC & Credit",
                "insert_after": "emergency_contact_phone",
                "collapsible": 1,
            },
            {"fieldname": "kyc_status", "fieldtype": "Select", "label": "KYC Status",
             "options": "Pending\nVerified\nRejected", "default": "Pending", "insert_after": "kyc_section"},
            {"fieldname": "credit_score", "fieldtype": "Int", "label": "Credit Score", "insert_after": "kyc_status"},
            {"fieldname": "blacklist_flag", "fieldtype": "Check", "label": "Blacklisted", "insert_after": "credit_score"},
            {"fieldname": "blacklist_reason", "fieldtype": "Small Text", "label": "Blacklist Reason",
             "insert_after": "blacklist_flag", "depends_on": "eval:doc.blacklist_flag == 1"},
        ]
    }
    try:
        create_custom_fields(custom_fields, ignore_validate=True, update=False)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Tenant custom fields setup failed: {e}", "Real Estate Setup")


def _create_workspace():
    """Create Real Estate workspace if it doesn't exist."""
    if frappe.db.exists("Workspace", "Real Estate"):
        return
    try:
        import json
        content = json.dumps([
            {"id": "re-props", "type": "card", "data": {"card_name": "Properties", "col": 4}},
            {"id": "re-leasing", "type": "card", "data": {"card_name": "Leasing", "col": 4}},
            {"id": "re-ops", "type": "card", "data": {"card_name": "Operations", "col": 4}},
        ])
        ws = frappe.new_doc("Workspace")
        ws.name = "Real Estate"
        ws.label = "Real Estate"
        ws.title = "Real Estate"
        ws.module = "Real Estate"
        ws.icon = "fa fa-home"
        ws.type = "module"
        ws.is_standard = 1
        ws.public = 1
        ws.content = content
        for link in [
            ("Property", "Property"), ("Property Unit", "Property Unit"),
            ("Lease Agreement", "Lease Agreement"), ("Rent Invoice", "Rent Invoice"),
            ("Maintenance Request", "Maintenance Request"), ("Property Inspection", "Property Inspection"),
            ("Owner Statement", "Owner Statement"), ("Property Listing", "Property Listing"),
            ("Visitor Lead Inquiry", "Visitor Lead Inquiry"), ("Sale Agreement", "Sale Agreement"),
            ("Agent", "Agent"), ("Security Deposit Ledger", "Security Deposit Ledger"),
            ("Utility Rate Card", "Utility Rate Card"),
        ]:
            ws.append("links", {
                "type": "Link", "label": link[0], "link_to": link[1],
                "link_type": "DocType", "onboard": 0, "is_query_report": 0
            })
        ws.flags.ignore_permissions = True
        ws.insert()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Workspace creation failed: {e}", "Real Estate Setup")


def _create_property_item():
    """Ensure the standard items used by billing exist."""
    for item_code, item_name in [
        ("Monthly Rent", "Monthly Rent"),
        ("Property Sale Milestone", "Property Sale Milestone"),
        ("Management Fee", "Property Management Fee"),
    ]:
        if frappe.db.exists("Item", item_code):
            continue
        try:
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = item_name
            item.item_group = "Services"
            item.is_stock_item = 0
            item.flags.ignore_permissions = True
            item.insert()
        except Exception:
            pass
    frappe.db.commit()
