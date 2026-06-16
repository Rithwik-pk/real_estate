frappe.ui.form.on('Sale Agreement', {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === 'Active') {
			frm.add_custom_button(__('Generate Milestone Invoices'), () => {
				frm.call('generate_milestone_invoices').then(r => {
					if (r.message && r.message.length) {
						frappe.show_alert({ message: __('{0} invoices created', [r.message.length]), indicator: 'green' });
						frm.reload_doc();
					} else {
						frappe.show_alert({ message: __('No pending milestones due today.'), indicator: 'blue' });
					}
				});
			}, __('Actions'));
		}
	},

	sale_price(frm) {
		if (!frm.doc.payment_schedule || !frm.doc.payment_schedule.length) {
			suggest_payment_schedule(frm);
		}
	},
});

function suggest_payment_schedule(frm) {
	if (!frm.doc.sale_price) return;
	const price = frm.doc.sale_price;
	const schedule = [
		{ milestone: 'Booking Advance (10%)', amount: price * 0.1 },
		{ milestone: 'On Agreement (30%)', amount: price * 0.3 },
		{ milestone: 'On Transfer (60%)', amount: price * 0.6 },
	];
	schedule.forEach(s => {
		frm.add_child('payment_schedule', { milestone: s.milestone, amount: s.amount, status: 'Pending' });
	});
	frm.refresh_field('payment_schedule');
}
