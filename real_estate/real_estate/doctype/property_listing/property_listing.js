frappe.ui.form.on('Property Listing', {
	refresh(frm) {
		frm.add_custom_button(__('View Inquiries'), () => {
			frappe.set_route('List', 'Visitor Lead Inquiry', { listing: frm.doc.name });
		}, __('View'));

		if (frm.doc.listing_status === 'Active' && !frm.doc.portal_published) {
			frm.add_custom_button(__('Publish to Portal'), () => {
				frm.set_value('portal_published', 1);
				frm.save();
			});
		}
	},
});
