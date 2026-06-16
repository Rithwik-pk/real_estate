import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate, date_diff


class LeaseAgreement(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname
        self.lease_no = make_autoname(self.naming_series)
        self.name = self.lease_no

    def validate(self):
        self._validate_dates()
        self._validate_payment_due_day()
        self._check_unit_availability()

    def before_submit(self):
        self.lease_status = "Active"

    def on_submit(self):
        self._mark_unit_occupied()
        self._create_security_deposit_entry()
        self._calculate_agent_commission()

    def on_cancel(self):
        self.lease_status = "Terminated"
        self._mark_unit_available()

    def on_update_after_submit(self):
        pass

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _validate_dates(self):
        if self.lease_start_date and self.lease_end_date:
            if getdate(self.lease_end_date) <= getdate(self.lease_start_date):
                frappe.throw(_("Lease end date must be after start date."))

    def _validate_payment_due_day(self):
        if self.payment_due_day and not (1 <= self.payment_due_day <= 28):
            frappe.throw(_("Payment due day must be between 1 and 28."))

    def _check_unit_availability(self):
        if self.docstatus == 0:
            active_lease = frappe.db.exists(
                "Lease Agreement",
                {
                    "property_unit": self.property_unit,
                    "lease_status": "Active",
                    "name": ("!=", self.name),
                    "docstatus": 1,
                },
            )
            if active_lease:
                frappe.throw(
                    _("Unit {0} already has an active lease: {1}").format(
                        self.property_unit, active_lease
                    )
                )

    def _mark_unit_occupied(self):
        frappe.db.set_value(
            "Property Unit",
            self.property_unit,
            {"status": "Occupied", "current_lease": self.name},
        )

    def _mark_unit_available(self):
        frappe.db.set_value(
            "Property Unit",
            self.property_unit,
            {"status": "Available", "current_lease": None},
        )

    def _create_security_deposit_entry(self):
        if not self.security_deposit:
            return
        deposit = frappe.new_doc("Security Deposit Ledger")
        deposit.lease_agreement = self.name
        deposit.property_unit = self.property_unit
        deposit.tenant = self.tenant
        deposit.transaction_type = "Received"
        deposit.amount = self.security_deposit
        deposit.transaction_date = self.lease_start_date
        deposit.remarks = f"Security deposit received for lease {self.name}"
        deposit.insert(ignore_permissions=True)

    def _calculate_agent_commission(self):
        if not self.agent:
            return
        agent = frappe.get_doc("Agent", self.agent)
        commission = (self.monthly_rent * (agent.commission_percent_rental or 0)) / 100
        if commission > 0:
            frappe.db.set_value("Agent", self.agent, "pending_commission",
                                (frappe.db.get_value("Agent", self.agent, "pending_commission") or 0) + commission)

    # ─── Whitelisted API methods ───────────────────────────────────────────────

    @frappe.whitelist()
    def renew_lease(self, new_end_date, apply_escalation=True):
        """Create a new lease from this one applying escalation."""
        new_rent = self.monthly_rent
        escalation_applied = 0
        if apply_escalation and self.escalation_percent:
            escalation_applied = self.escalation_percent
            new_rent = self.monthly_rent * (1 + self.escalation_percent / 100)

        new_lease = frappe.copy_doc(self)
        new_lease.lease_start_date = add_days(self.lease_end_date, 1)
        new_lease.lease_end_date = new_end_date
        new_lease.monthly_rent = new_rent
        new_lease.lease_status = "Draft"
        new_lease.docstatus = 0
        new_lease.renewal_history = []
        new_lease.insert(ignore_permissions=True)

        self.append("renewal_history", {
            "renewal_date": nowdate(),
            "previous_lease": self.name,
            "new_rent": new_rent,
            "new_end_date": new_end_date,
            "escalation_applied": escalation_applied,
        })
        self.lease_status = "Renewed"
        self.save(ignore_permissions=True)

        return new_lease.name

    @frappe.whitelist()
    def generate_clauses(self, special_requirements=""):
        """Generate AI lease clauses."""
        from real_estate.ai.lease_clauses import generate_lease_clauses
        clauses = generate_lease_clauses(
            lease_type=self.lease_type,
            country=frappe.db.get_value("Property Unit", self.property_unit, "property"),
            special_requirements=special_requirements,
        )
        return clauses

    @frappe.whitelist()
    def terminate_lease(self, termination_date=None, reason=""):
        if self.docstatus != 1:
            frappe.throw(_("Only submitted leases can be terminated."))
        self.cancel()
        frappe.db.set_value(
            "Lease Agreement", self.name, "lease_status", "Terminated"
        )
        self._initiate_deposit_refund(termination_date, reason)

    def _initiate_deposit_refund(self, termination_date, reason):
        if not self.security_deposit:
            return
        deposit_held = frappe.db.get_value(
            "Security Deposit Ledger",
            {"lease_agreement": self.name, "transaction_type": "Received"},
            "amount",
        ) or 0
        if deposit_held <= 0:
            return
        refund = frappe.new_doc("Security Deposit Ledger")
        refund.lease_agreement = self.name
        refund.property_unit = self.property_unit
        refund.tenant = self.tenant
        refund.transaction_type = "Refunded"
        refund.amount = deposit_held
        refund.transaction_date = termination_date or nowdate()
        refund.remarks = reason or "Lease terminated — deposit refund initiated"
        refund.insert(ignore_permissions=True)
