frappe.ui.form.on('Visitor Lead Inquiry', {
	refresh(frm) {
		const statuses = ['New', 'Contacted', 'Visit Scheduled', 'Offer Made', 'Converted', 'Lost'];
		const idx = statuses.indexOf(frm.doc.status);
		if (idx >= 0 && idx < statuses.length - 2) {
			frm.add_custom_button(__(statuses[idx + 1]), () => {
				frm.set_value('status', statuses[idx + 1]);
				frm.save();
			}, __('Advance Status'));
		}
		if (frm.doc.status === 'Offer Made') {
			frm.add_custom_button(__('Create Lease'), () => {
				frappe.new_doc('Lease Agreement', {
					tenant: frm.doc.linked_crm_lead,
					property_unit: frm.doc.listing,
				});
			}, __('Actions'));
		}
		if (frm.doc.linked_crm_lead) {
			frm.add_custom_button(__('View CRM Lead'), () => {
				frappe.set_route('Form', 'CRM Lead', frm.doc.linked_crm_lead);
			}, __('View'));
		}
	},
});
