from frappe import _


def get_data():
    return [
        {
            "module_name": "Real Estate",
            "color": "#4CAF50",
            "icon": "octicon octicon-home",
            "type": "module",
            "label": _("Real Estate"),
            "description": _("Property management, leasing, and portfolio analytics."),
        }
    ]
