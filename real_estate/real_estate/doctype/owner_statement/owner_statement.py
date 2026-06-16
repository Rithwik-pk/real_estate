import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, get_last_day, getdate


class OwnerStatement(Document):
    def validate(self):
        self._calculate_totals()

    def before_submit(self):
        self._calculate_totals()

    def on_submit(self):
        self._create_journal_entry()
        self._generate_ai_narrative()

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _calculate_totals(self):
        self.management_fee_amount = flt(self.gross_rent_collected) * flt(self.management_fee_percent) / 100
        self.net_payout = (
            flt(self.gross_rent_collected)
            - flt(self.maintenance_costs)
            - flt(self.management_fee_amount)
        )

    def _create_journal_entry(self):
        if self.linked_journal_entry:
            return
        company = (
            frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
        )
        if not company or self.net_payout <= 0:
            return
        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.statement_month
        je.company = company
        je.voucher_type = "Journal Entry"
        je.user_remark = f"Owner Statement {self.name} — Net payout to {self.owner}"
        receivable_account = frappe.db.get_value(
            "Company", company, "default_receivable_account"
        )
        payable_account = frappe.db.get_value(
            "Company", company, "default_payable_account"
        )
        if receivable_account and payable_account:
            je.append("accounts", {
                "account": receivable_account,
                "debit_in_account_currency": self.net_payout,
                "party_type": "Customer",
                "party": self.owner,
            })
            je.append("accounts", {
                "account": payable_account,
                "credit_in_account_currency": self.net_payout,
            })
            je.flags.ignore_permissions = True
            je.insert()
            self.db_set("linked_journal_entry", je.name)

    def _generate_ai_narrative(self):
        try:
            from real_estate.ai.owner_narrative import generate_owner_narrative
            narrative = generate_owner_narrative(self)
            if narrative:
                self.db_set("ai_narrative", narrative)
        except Exception as e:
            frappe.log_error(f"AI narrative generation failed: {e}", "Owner Statement AI")

    @frappe.whitelist()
    def compute_from_invoices(self):
        """Auto-populate financials from Rent Invoices for the statement month."""
        month_start = get_first_day(self.statement_month)
        month_end = get_last_day(self.statement_month)
        invoices = frappe.get_all(
            "Rent Invoice",
            filters={
                "docstatus": 1,
                "status": "Paid",
                "billing_period_start": (">=", month_start),
                "billing_period_end": ("<=", month_end),
            },
            fields=["name", "total_amount", "lease"],
        )
        # Filter invoices for this property
        property_units = frappe.get_all(
            "Property Unit", filters={"property": self.property}, pluck="name"
        )
        property_leases = frappe.get_all(
            "Lease Agreement",
            filters={"property_unit": ("in", property_units), "docstatus": 1},
            pluck="name",
        )
        total = sum(
            flt(inv.total_amount) for inv in invoices if inv.lease in property_leases
        )
        maintenance = frappe.db.sql(
            """
            SELECT IFNULL(SUM(actual_cost), 0)
            FROM `tabMaintenance Request`
            WHERE property_unit IN %(units)s
            AND completion_date BETWEEN %(start)s AND %(end)s
            AND status = 'Completed'
            """,
            {"units": property_units, "start": month_start, "end": month_end},
        )[0][0]
        self.gross_rent_collected = total
        self.maintenance_costs = flt(maintenance)
        self._calculate_totals()
        self.save(ignore_permissions=True)
        return {"gross_rent_collected": self.gross_rent_collected, "net_payout": self.net_payout}
