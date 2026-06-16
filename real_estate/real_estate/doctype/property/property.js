frappe.ui.form.on('Property', {
	refresh(frm) {
		frm.add_custom_button(__('View Units'), () => {
			frappe.set_route('List', 'Property Unit', { property: frm.doc.name });
		}, __('Actions'));

		frm.add_custom_button(__('Add Maintenance Request'), () => {
			frappe.new_doc('Maintenance Request', { property: frm.doc.name });
		}, __('Actions'));

		frm.add_custom_button(__('Owner Statement'), () => {
			frappe.set_route('List', 'Owner Statement', { property: frm.doc.name });
		}, __('Reports'));

		if (frm.doc.status === 'Available') {
			frm.dashboard.set_headline(__('This property has available units.'));
		}
	},

	property_type(frm) {
		frm.set_value('status', 'Available');
	},
});
