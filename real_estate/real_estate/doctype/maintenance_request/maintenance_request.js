frappe.ui.form.on('Maintenance Request', {
	refresh(frm) {
		const status_flow = {
			'Open': ['Assigned', 'Cancelled'],
			'Assigned': ['In Progress', 'Cancelled'],
			'In Progress': ['Pending Parts', 'Completed', 'Cancelled'],
			'Pending Parts': ['In Progress', 'Completed', 'Cancelled'],
		};
		const next = status_flow[frm.doc.status] || [];
		next.forEach(s => {
			frm.add_custom_button(__(s), () => {
				frm.set_value('status', s);
				frm.save();
			}, __('Update Status'));
		});

		if (frm.doc.priority === 'Emergency') {
			frm.dashboard.set_headline_alert(
				'<span class="indicator red">Emergency Request — Immediate attention required</span>'
			);
		}
	},

	status(frm) {
		if (frm.doc.status === 'Completed' && !frm.doc.completion_date) {
			frm.set_value('completion_date', frappe.datetime.nowdate());
		}
	},
});
