frappe.ui.form.on('Lease Agreement', {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.lease_status === 'Active') {
			frm.add_custom_button(__('Renew Lease'), () => {
				show_renewal_dialog(frm);
			}, __('Actions'));

			frm.add_custom_button(__('Terminate Lease'), () => {
				show_termination_dialog(frm);
			}, __('Actions'));

			frm.add_custom_button(__('Create Rent Invoice'), () => {
				frappe.call({
					method: 'real_estate.tasks.rent_billing.create_invoice_for_lease',
					args: { lease_name: frm.doc.name },
					callback: r => {
						if (r.message) {
							frappe.set_route('Form', 'Rent Invoice', r.message);
						}
					},
				});
			}, __('Actions'));
		}

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Generate Clauses (AI)'), () => {
				show_clause_dialog(frm);
			}, __('AI'));
		}

		frm.add_custom_button(__('Rent Invoices'), () => {
			frappe.set_route('List', 'Rent Invoice', { lease: frm.doc.name });
		}, __('View'));
	},

	lease_start_date(frm) {
		calculate_days(frm);
	},

	lease_end_date(frm) {
		calculate_days(frm);
	},

	monthly_rent(frm) {
		calculate_security_deposit(frm);
	},
});

function calculate_days(frm) {
	if (frm.doc.lease_start_date && frm.doc.lease_end_date) {
		const start = frappe.datetime.str_to_obj(frm.doc.lease_start_date);
		const end = frappe.datetime.str_to_obj(frm.doc.lease_end_date);
		const days = frappe.datetime.get_diff(end, start);
		frm.dashboard.set_headline(__('Lease Duration: {0} days ({1} months)', [days, Math.round(days / 30)]));
	}
}

function calculate_security_deposit(frm) {
	if (!frm.doc.security_deposit && frm.doc.monthly_rent) {
		frm.set_value('security_deposit', frm.doc.monthly_rent * 2);
	}
}

function show_renewal_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Renew Lease'),
		fields: [
			{ fieldname: 'new_end_date', fieldtype: 'Date', label: __('New End Date'), reqd: 1 },
			{ fieldname: 'apply_escalation', fieldtype: 'Check', label: __('Apply Escalation ({0}%)', [frm.doc.escalation_percent || 0]), default: 1 },
		],
		primary_action_label: __('Renew'),
		primary_action(values) {
			frm.call('renew_lease', {
				new_end_date: values.new_end_date,
				apply_escalation: values.apply_escalation,
			}).then(r => {
				if (r.message) {
					d.hide();
					frappe.set_route('Form', 'Lease Agreement', r.message);
				}
			});
		},
	});
	d.show();
}

function show_termination_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Terminate Lease'),
		fields: [
			{ fieldname: 'termination_date', fieldtype: 'Date', label: __('Termination Date'), reqd: 1, default: frappe.datetime.nowdate() },
			{ fieldname: 'reason', fieldtype: 'Small Text', label: __('Reason') },
		],
		primary_action_label: __('Terminate'),
		primary_action(values) {
			frappe.confirm(__('This will cancel the lease and initiate deposit refund. Proceed?'), () => {
				frm.call('terminate_lease', {
					termination_date: values.termination_date,
					reason: values.reason,
				}).then(() => {
					d.hide();
					frm.reload_doc();
				});
			});
		},
	});
	d.show();
}

function show_clause_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Generate Lease Clauses (AI)'),
		fields: [
			{ fieldname: 'special_requirements', fieldtype: 'Small Text', label: __('Special Requirements (optional)') },
		],
		primary_action_label: __('Generate'),
		primary_action(values) {
			frappe.show_alert({ message: __('Generating clauses with AI...'), indicator: 'blue' });
			frm.call('generate_clauses', { special_requirements: values.special_requirements || '' })
				.then(r => {
					if (r.message) {
						frm.set_value('special_clauses', r.message);
						d.hide();
						frappe.show_alert({ message: __('Clauses generated — please review before saving.'), indicator: 'green' });
					}
				});
		},
	});
	d.show();
}
