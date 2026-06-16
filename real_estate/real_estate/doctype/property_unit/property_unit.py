import frappe
from frappe import _
from frappe.model.document import Document


class PropertyUnit(Document):
    def autoname(self):
        if not self.unit_code:
            prefix = frappe.db.get_value("Property", self.property, "property_code") or "UNIT"
            count = frappe.db.count("Property Unit", {"property": self.property})
            self.unit_code = f"{prefix}-U{str(count + 1).zfill(3)}"

    def validate(self):
        self._validate_rent()

    def _validate_rent(self):
        if self.rent_amount and self.rent_amount < 0:
            frappe.throw(_("Rent amount cannot be negative."))
        if self.sale_price and self.sale_price < 0:
            frappe.throw(_("Sale price cannot be negative."))

    @frappe.whitelist()
    def suggest_rent(self):
        from real_estate.ai.rent_valuation import suggest_rent_for_unit
        return suggest_rent_for_unit(self.name)
