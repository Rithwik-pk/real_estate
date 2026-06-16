frappe.ui.form.on('Security Deposit Ledger', {
	refresh(frm) {
		if (frm.doc.linked_journal_entry) {
			frm.add_custom_button(__('Journal Entry'), () => {
				frappe.set_route('Form', 'Journal Entry', frm.doc.linked_journal_entry);
			}, __('Links'));
		}

		if (frm.doc.lease_agreement) {
			frm.add_custom_button(__('Lease Agreement'), () => {
				frappe.set_route('Form', 'Lease Agreement', frm.doc.lease_agreement);
			}, __('Links'));
		}

		if (!frm.doc.__islocal && frm.doc.transaction_type === 'Received') {
			frm.add_custom_button(__('Create Refund'), () => {
				frappe.prompt([
					{ fieldname: 'amount', fieldtype: 'Currency', label: 'Refund Amount', reqd: 1,
					  default: frm.doc.amount },
					{ fieldname: 'transaction_date', fieldtype: 'Date', label: 'Refund Date', reqd: 1,
					  default: frappe.datetime.get_today() },
					{ fieldname: 'remarks', fieldtype: 'Small Text', label: 'Remarks',
					  default: `Refund of deposit for lease ${frm.doc.lease_agreement}` },
				], (vals) => {
					frappe.new_doc('Security Deposit Ledger', {
						lease_agreement: frm.doc.lease_agreement,
						tenant: frm.doc.tenant,
						transaction_type: 'Refunded',
						amount: vals.amount,
						transaction_date: vals.transaction_date,
						remarks: vals.remarks,
					});
				}, __('Create Deposit Refund'), __('Create'));
			}, __('Actions'));

			frm.add_custom_button(__('Create Deduction'), () => {
				frappe.prompt([
					{ fieldname: 'amount', fieldtype: 'Currency', label: 'Deduction Amount', reqd: 1 },
					{ fieldname: 'transaction_date', fieldtype: 'Date', label: 'Date', reqd: 1,
					  default: frappe.datetime.get_today() },
					{ fieldname: 'remarks', fieldtype: 'Small Text', label: 'Reason for Deduction', reqd: 1 },
				], (vals) => {
					frappe.new_doc('Security Deposit Ledger', {
						lease_agreement: frm.doc.lease_agreement,
						tenant: frm.doc.tenant,
						transaction_type: 'Deducted',
						amount: vals.amount,
						transaction_date: vals.transaction_date,
						remarks: vals.remarks,
					});
				}, __('Create Deduction'), __('Create'));
			}, __('Actions'));
		}

		// Colour-code the form header by transaction type
		const colours = {
			'Received': 'green',
			'Refunded': 'orange',
			'Deducted': 'red',
		};
		if (colours[frm.doc.transaction_type]) {
			frm.page.set_indicator(frm.doc.transaction_type, colours[frm.doc.transaction_type]);
		}
	},
});
