frappe.ui.form.on('Agent', {
	refresh(frm) {
		if (frm.doc.pending_commission > 0) {
			frm.dashboard.set_headline(
				__('Pending commission: {0}', [format_currency(frm.doc.pending_commission)])
			);
		}
		frm.add_custom_button(__('View Leases'), () => {
			frappe.set_route('List', 'Lease Agreement', { agent: frm.doc.name });
		}, __('View'));
		frm.add_custom_button(__('View Sale Agreements'), () => {
			frappe.set_route('List', 'Sale Agreement', { agent: frm.doc.name });
		}, __('View'));
	},
});
