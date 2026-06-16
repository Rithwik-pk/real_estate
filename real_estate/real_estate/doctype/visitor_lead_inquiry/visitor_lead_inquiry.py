import frappe
from frappe.model.document import Document


class VisitorLeadInquiry(Document):
    def after_insert(self):
        self._increment_inquiry_count()
        self._create_crm_lead()

    def _increment_inquiry_count(self):
        if self.listing:
            count = frappe.db.get_value("Property Listing", self.listing, "inquiry_count") or 0
            frappe.db.set_value("Property Listing", self.listing, "inquiry_count", count + 1)

    def _create_crm_lead(self):
        if frappe.db.exists("DocType", "CRM Lead") and not self.linked_crm_lead:
            try:
                lead = frappe.new_doc("CRM Lead")
                lead.lead_name = self.visitor_name
                lead.mobile_no = self.phone
                lead.email_id = self.email
                lead.source = self.source or "Website"
                lead.notes = self.message
                lead.flags.ignore_permissions = True
                lead.insert()
                self.db_set("linked_crm_lead", lead.name)
            except Exception as e:
                frappe.log_error(f"CRM Lead creation failed: {e}", "Visitor Inquiry")

    @frappe.whitelist()
    def convert_to_lease(self):
        if not self.listing:
            return
        unit = frappe.db.get_value("Property Listing", self.listing, "property_unit")
        return frappe.new_doc("Lease Agreement", {"property_unit": unit}).as_dict()
