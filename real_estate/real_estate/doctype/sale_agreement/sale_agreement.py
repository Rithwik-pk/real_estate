import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


class SaleAgreement(Document):
    def validate(self):
        self._validate_schedule()

    def on_submit(self):
        self.status = "Active"
        self._calculate_agent_commission()
        self._mark_unit_reserved()

    def on_cancel(self):
        self.status = "Cancelled"
        frappe.db.set_value("Property Unit", self.property_unit, "status", "Available")

    def _validate_schedule(self):
        total = sum(row.amount for row in self.payment_schedule)
        if self.payment_schedule and abs(total - self.sale_price) > 1:
            frappe.throw(
                _("Payment schedule total ({0}) must equal sale price ({1}).").format(
                    total, self.sale_price
                )
            )

    def _calculate_agent_commission(self):
        if not self.agent:
            return
        agent = frappe.get_doc("Agent", self.agent)
        commission = (self.sale_price * (agent.commission_percent_sale or 0)) / 100
        if commission > 0:
            current = frappe.db.get_value("Agent", self.agent, "pending_commission") or 0
            frappe.db.set_value("Agent", self.agent, "pending_commission", current + commission)

    def _mark_unit_reserved(self):
        frappe.db.set_value("Property Unit", self.property_unit, "status", "Reserved")

    @frappe.whitelist()
    def generate_milestone_invoices(self):
        """Create Sales Invoices for all pending milestones whose due_date <= today."""
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        created = []
        for row in self.payment_schedule:
            if row.status == "Pending" and getdate(row.due_date) <= getdate(nowdate()):
                si = frappe.new_doc("Sales Invoice")
                si.customer = self.buyer
                si.company = company
                si.posting_date = row.due_date
                si.append("items", {
                    "item_code": "Property Sale Milestone",
                    "qty": 1,
                    "rate": row.amount,
                    "description": f"{row.milestone} — {self.name}",
                })
                si.flags.ignore_permissions = True
                si.insert()
                row.status = "Invoiced"
                row.linked_invoice = si.name
                created.append(si.name)
        if created:
            self.save(ignore_permissions=True)
        return created
