frappe.ui.form.on('Property Unit', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Suggest Rent (AI)'), () => {
				frm.call('suggest_rent').then(r => {
					if (r.message) {
						const d = r.message;
						frappe.msgprint({
							title: __('AI Rent Suggestion'),
							message: `
								<div class="p-3">
									<p><strong>${__('Suggested Range')}:</strong>
										${format_currency(d.min, frm.doc.currency)} – ${format_currency(d.max, frm.doc.currency)}
									</p>
									<p><strong>${__('Reasoning')}:</strong> ${d.reasoning}</p>
									${d.comparables ? `<p><strong>${__('Comparables')}:</strong> ${d.comparables}</p>` : ''}
								</div>
							`,
							wide: true,
						});
					}
				});
			}, __('AI'));

			frm.add_custom_button(__('New Lease'), () => {
				frappe.new_doc('Lease Agreement', {
					property_unit: frm.doc.name,
					monthly_rent: frm.doc.rent_amount,
				});
			}, __('Actions'));

			frm.add_custom_button(__('New Maintenance Request'), () => {
				frappe.new_doc('Maintenance Request', { property_unit: frm.doc.name });
			}, __('Actions'));

			frm.add_custom_button(__('New Inspection'), () => {
				frappe.new_doc('Property Inspection', { property_unit: frm.doc.name });
			}, __('Actions'));

			frm.add_custom_button(__('Create Listing'), () => {
				frappe.new_doc('Property Listing', {
					property_unit: frm.doc.name,
					asking_price: frm.doc.sale_price || frm.doc.rent_amount,
				});
			}, __('Actions'));
		}
	},
});
