"""AI rent valuation assistant (Feature K)."""
import json
import frappe
from .claude_client import call_claude


@frappe.whitelist()
def suggest_rent_for_unit(unit_name: str) -> dict:
    """
    Gather unit data and comparable units, then ask Claude for a rent range.
    Returns: {min, max, reasoning, comparables}
    """
    unit = frappe.get_doc("Property Unit", unit_name)
    property_doc = frappe.get_doc("Property", unit.property)

    comparables = frappe.get_all(
        "Property Unit",
        filters={
            "property": unit.property,
            "unit_type": unit.unit_type,
            "status": "Occupied",
            "name": ("!=", unit_name),
        },
        fields=["unit_number", "area_sqft", "floor", "rent_amount", "furnishing_status"],
        limit=5,
    )

    comparable_text = "\n".join(
        f"  - Unit {c.unit_number}: {c.area_sqft} sqft, floor {c.floor}, "
        f"{c.furnishing_status}, rent {c.rent_amount}"
        for c in comparables
    ) or "  No comparable units available in same property."

    amenities = ", ".join([f.feature for f in property_doc.amenities]) if hasattr(property_doc, "amenities") else "N/A"

    prompt = f"""You are an expert real estate valuation AI. Suggest a monthly rent range for this unit.

Property Details:
- Property Name: {property_doc.property_name}
- Property Type: {property_doc.property_type}
- City: {property_doc.city or 'N/A'}
- Amenities: {amenities}

Unit Details:
- Unit Type: {unit.unit_type}
- Area: {unit.area_sqft or 'N/A'} sqft
- Floor: {unit.floor or 'N/A'}
- Furnishing: {unit.furnishing_status or 'Unfurnished'}

Comparable units in same property:
{comparable_text}

Provide your analysis in this exact JSON format:
{{
  "min": <number>,
  "max": <number>,
  "reasoning": "<2-3 sentence explanation>",
  "comparables": "<brief note on comparable data used>"
}}"""

    response = call_claude(prompt, max_tokens=512)
    if not response:
        return {
            "min": 0, "max": 0,
            "reasoning": "AI valuation unavailable. Please check Claude API configuration.",
            "comparables": "",
        }
    try:
        # Extract JSON from potential surrounding text
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except Exception:
        return {"min": 0, "max": 0, "reasoning": response, "comparables": ""}
