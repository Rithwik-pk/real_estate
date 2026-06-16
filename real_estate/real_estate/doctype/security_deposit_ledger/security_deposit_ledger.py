import frappe
from frappe.model.document import Document


class SecurityDepositLedger(Document):
    def after_insert(self):
        self._create_journal_entry()

    def _create_journal_entry(self):
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )
        if not company:
            return
        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.transaction_date
        je.company = company
        je.voucher_type = "Journal Entry"
        je.user_remark = f"Security Deposit — {self.transaction_type} — {self.lease_agreement}"
        deposit_account = self._get_deposit_account(company)
        cash_account = frappe.db.get_value("Company", company, "default_cash_account")
        if deposit_account and cash_account:
            if self.transaction_type == "Received":
                je.append("accounts", {"account": cash_account, "debit_in_account_currency": self.amount})
                je.append("accounts", {"account": deposit_account, "credit_in_account_currency": self.amount})
            elif self.transaction_type in ("Refunded", "Deducted"):
                je.append("accounts", {"account": deposit_account, "debit_in_account_currency": self.amount})
                je.append("accounts", {"account": cash_account, "credit_in_account_currency": self.amount})
            je.flags.ignore_permissions = True
            je.insert()
            self.db_set("linked_journal_entry", je.name)

    def _get_deposit_account(self, company):
        acc = frappe.db.get_value("Account", {"account_name": "Security Deposits", "company": company})
        if not acc:
            parent = frappe.db.get_value("Account", {"account_type": "Liability", "company": company, "is_group": 1})
            if parent:
                new_acc = frappe.new_doc("Account")
                new_acc.account_name = "Security Deposits"
                new_acc.parent_account = parent
                new_acc.company = company
                new_acc.account_type = "Liability"
                new_acc.flags.ignore_permissions = True
                new_acc.insert()
                return new_acc.name
        return acc
