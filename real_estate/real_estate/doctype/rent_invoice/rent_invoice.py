import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate


class RentInvoice(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname
        self.invoice_no = make_autoname(self.naming_series)
        self.name = self.invoice_no

    def validate(self):
        self._fetch_tenant_from_lease()
        self._calculate_utility_totals()
        self._calculate_totals()

    def before_submit(self):
        self._validate_totals()

    def on_submit(self):
        self._create_sales_invoice()

    def on_cancel(self):
        self._cancel_sales_invoice()
        self.status = "Unpaid"

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _fetch_tenant_from_lease(self):
        if self.lease and not self.tenant:
            self.tenant = frappe.db.get_value("Lease Agreement", self.lease, "tenant")

    def _calculate_utility_totals(self):
        for row in self.utility_charges:
            if row.previous_reading is not None and row.current_reading is not None:
                row.consumption = flt(row.current_reading) - flt(row.previous_reading)
                row.amount = flt(row.consumption) * flt(row.rate_per_unit)

    def _calculate_totals(self):
        utility_total = sum(flt(row.amount) for row in self.utility_charges)
        self.subtotal = flt(self.base_rent) + utility_total + flt(self.late_fee) - flt(self.discount)
        self.vat_amount = flt(self.subtotal) * flt(self.vat_percent) / 100
        self.total_amount = self.subtotal + self.vat_amount

    def _validate_totals(self):
        if self.total_amount <= 0:
            frappe.throw(_("Total amount must be greater than zero."))

    def _create_sales_invoice(self):
        """Create corresponding ERPNext Sales Invoice."""
        if self.linked_sales_invoice:
            return
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            return
        si = frappe.new_doc("Sales Invoice")
        si.customer = self.tenant
        si.posting_date = nowdate()
        si.due_date = nowdate()
        si.company = company
        si.append("items", {
            "item_code": self._get_or_create_rent_item(),
            "qty": 1,
            "rate": self.total_amount,
            "description": f"Rent for period {self.billing_period_start} to {self.billing_period_end}",
        })
        si.flags.ignore_permissions = True
        si.insert()
        self.db_set("linked_sales_invoice", si.name)

    def _get_or_create_rent_item(self):
        if frappe.db.exists("Item", "Monthly Rent"):
            return "Monthly Rent"
        item = frappe.new_doc("Item")
        item.item_code = "Monthly Rent"
        item.item_name = "Monthly Rent"
        item.item_group = "Services"
        item.is_stock_item = 0
        item.flags.ignore_permissions = True
        item.insert()
        return item.name

    def _cancel_sales_invoice(self):
        if self.linked_sales_invoice:
            si = frappe.get_doc("Sales Invoice", self.linked_sales_invoice)
            if si.docstatus == 1:
                si.cancel()

    # ─── Whitelisted ──────────────────────────────────────────────────────────

    @frappe.whitelist()
    def record_payment(self, amount, payment_method, payment_date=None):
        paid = flt(amount)
        if paid >= self.total_amount:
            self.status = "Paid"
        elif paid > 0:
            self.status = "Partially Paid"
        self.payment_method = payment_method
        self.payment_date = payment_date or nowdate()
        self.save(ignore_permissions=True)
        return self.status
