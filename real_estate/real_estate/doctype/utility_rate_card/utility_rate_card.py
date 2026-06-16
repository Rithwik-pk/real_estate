import frappe
from frappe.model.document import Document
from frappe.utils import flt


class UtilityRateCard(Document):
    def calculate_cost(self, consumption):
        """Calculate cost for a given consumption using slab rates."""
        total = 0.0
        remaining = flt(consumption)
        sorted_slabs = sorted(self.slabs, key=lambda s: s.from_units)
        for slab in sorted_slabs:
            if remaining <= 0:
                break
            slab_max = flt(slab.to_units) if slab.to_units else float("inf")
            slab_units = min(remaining, slab_max - flt(slab.from_units))
            total += slab_units * flt(slab.rate_per_unit)
            remaining -= slab_units
        return total
