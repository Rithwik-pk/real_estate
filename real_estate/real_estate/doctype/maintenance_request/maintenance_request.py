import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


class MaintenanceRequest(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname
        self.request_no = make_autoname(self.naming_series)
        self.name = self.request_no

    def validate(self):
        self._set_completion_date()
        self._notify_on_emergency()

    def after_insert(self):
        self._notify_property_manager()

    def _set_completion_date(self):
        if self.status == "Completed" and not self.completion_date:
            self.completion_date = nowdate()

    def _notify_on_emergency(self):
        if self.priority == "Emergency" and self.status == "Open":
            frappe.publish_realtime(
                "real_estate_emergency_maintenance",
                {"request": self.name, "unit": self.property_unit},
                user="Administrator",
            )

    def _notify_property_manager(self):
        managers = frappe.get_all(
            "Has Role",
            filters={"role": "Property Manager", "parenttype": "User"},
            pluck="parent",
        )
        for manager in managers:
            frappe.sendmail(
                recipients=[manager],
                subject=f"New Maintenance Request: {self.name} ({self.priority})",
                message=f"""
                    <p>A new maintenance request has been submitted:</p>
                    <ul>
                        <li><strong>Unit:</strong> {self.property_unit}</li>
                        <li><strong>Category:</strong> {self.category}</li>
                        <li><strong>Priority:</strong> {self.priority}</li>
                        <li><strong>Description:</strong> {self.description or ''}</li>
                    </ul>
                """,
                now=True,
            )

    @frappe.whitelist()
    def assign_to_vendor(self, vendor, assigned_to=None, estimated_cost=None):
        self.vendor = vendor
        if assigned_to:
            self.assigned_to = assigned_to
        if estimated_cost:
            self.estimated_cost = estimated_cost
        self.status = "Assigned"
        self.save(ignore_permissions=True)
