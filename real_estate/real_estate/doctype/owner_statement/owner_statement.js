frappe.ui.form.on('Owner Statement', {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Compute from Invoices'), () => {
				frm.call('compute_from_invoices').then(r => {
					if (r.message) {
						frm.reload_doc();
						frappe.show_alert({ message: __('Financials computed from paid invoices.'), indicator: 'green' });
					}
				});
			});
		}
		if (frm.doc.linked_journal_entry) {
			frm.add_custom_button(__('View Journal Entry'), () => {
				frappe.set_route('Form', 'Journal Entry', frm.doc.linked_journal_entry);
			}, __('View'));
		}
		frm.set_df_property('net_payout', 'bold', 1);
	},

	gross_rent_collected(frm) { calculate_net(frm); },
	maintenance_costs(frm) { calculate_net(frm); },
	management_fee_percent(frm) { calculate_net(frm); },
});

function calculate_net(frm) {
	const fee = (frm.doc.gross_rent_collected || 0) * (frm.doc.management_fee_percent || 0) / 100;
	frm.set_value('management_fee_amount', fee);
	frm.set_value('net_payout',
		(frm.doc.gross_rent_collected || 0) - (frm.doc.maintenance_costs || 0) - fee
	);
}
