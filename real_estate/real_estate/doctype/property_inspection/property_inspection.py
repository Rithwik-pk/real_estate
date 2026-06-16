import frappe
from frappe.model.document import Document


CHECKLIST_TEMPLATES = {
    "Move-In": ["Walls & Ceilings", "Flooring", "Windows & Doors", "Kitchen Appliances",
                "Bathroom Fixtures", "Electrical Outlets", "Plumbing", "AC/Heating",
                "Smoke Detectors", "Locks & Keys"],
    "Move-Out": ["Walls & Ceilings", "Flooring", "Windows & Doors", "Kitchen Appliances",
                 "Bathroom Fixtures", "Electrical Outlets", "Plumbing", "AC/Heating",
                 "Smoke Detectors", "Cleanliness", "Damages"],
    "Periodic": ["General Cleanliness", "AC Filters", "Plumbing Leaks",
                 "Electrical Safety", "Fire Extinguisher", "Common Areas"],
    "Pre-Sale": ["Structural Integrity", "Roof Condition", "Foundation", "Electrical System",
                 "Plumbing System", "HVAC", "Insulation", "Exterior"],
}


class PropertyInspection(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname
        self.inspection_no = make_autoname(self.naming_series)
        self.name = self.inspection_no

    def after_insert(self):
        if self.inspection_type and not self.checklist:
            self._populate_checklist()
            self.save(ignore_permissions=True)

    def _populate_checklist(self):
        items = CHECKLIST_TEMPLATES.get(self.inspection_type, [])
        for item in items:
            self.append("checklist", {"item": item, "condition": "Good"})

    def validate(self):
        if self.action_required and not self.linked_maintenance_request:
            frappe.msgprint(
                "Action is required — consider creating a Maintenance Request.",
                alert=True,
            )
