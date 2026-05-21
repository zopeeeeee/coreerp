# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""boot_session hook — inject CoreERP context into the desk boot payload."""

import frappe


def boot_session(bootinfo):
	"""Add the user's organization context so the client can scope UI immediately."""
	from coreerp.organization.tenant import get_allowed_organizations, get_default_organization

	user = frappe.session.user
	bootinfo.coreerp = {
		"default_organization": get_default_organization(user),
		"organizations": get_allowed_organizations(user),
		"tenant_isolation": bool(
			frappe.db.get_single_value("CoreERP Settings", "enable_tenant_isolation")
		),
	}
