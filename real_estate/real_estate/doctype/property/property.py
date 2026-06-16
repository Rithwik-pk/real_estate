import frappe
from frappe.model.document import Document


class Property(Document):
    def autoname(self):
        if not self.property_code:
            self.property_code = frappe.generate_hash(length=8).upper()

    def validate(self):
        self._validate_area()

    def _validate_area(self):
        if self.built_up_area and self.total_area_sqft:
            if self.built_up_area > self.total_area_sqft:
                frappe.throw("Built-up area cannot exceed total area.")

    def on_update(self):
        self._sync_unit_status()

    def _sync_unit_status(self):
        units = frappe.get_all(
            "Property Unit",
            filters={"property": self.name, "status": "Available"},
            pluck="name",
        )
        if units:
            self.db_set("status", "Available", update_modified=False)
