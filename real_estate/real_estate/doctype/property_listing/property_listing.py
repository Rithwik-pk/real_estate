import frappe
from frappe.model.document import Document


class PropertyListing(Document):
    def validate(self):
        if self.listing_status in ("Sold", "Rented") and self.portal_published:
            self.portal_published = 0
            frappe.msgprint("Listing automatically unpublished from portal.", alert=True)

    def on_update(self):
        self._sync_unit_status()

    def _sync_unit_status(self):
        status_map = {
            "Sold": "Occupied",
            "Rented": "Occupied",
            "Active": "Available",
            "Withdrawn": "Available",
        }
        unit_status = status_map.get(self.listing_status)
        if unit_status:
            frappe.db.set_value("Property Unit", self.property_unit, "status", unit_status)
