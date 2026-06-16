frappe.ui.form.on('Property Inspection', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.action_required && !frm.doc.linked_maintenance_request) {
			frm.add_custom_button(__('Create Maintenance Request'), () => {
				frappe.new_doc('Maintenance Request', {
					property_unit: frm.doc.property_unit,
					description: `Follow-up from Inspection ${frm.doc.name} (${frm.doc.inspection_type})`,
				});
			});
		}
	},

	overall_condition(frm) {
		if (frm.doc.overall_condition === 'Poor') {
			frm.set_value('action_required', 1);
			frappe.show_alert({ message: __('Poor condition detected — action required flag set.'), indicator: 'orange' });
		}
	},
});
