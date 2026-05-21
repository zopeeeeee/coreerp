# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
CoreERP public REST API namespace.

These are thin, whitelisted helpers a SaaS frontend / portal / external integration
can call. Everything here respects Frappe permissions and tenant scoping.

Call as:  /api/method/coreerp.api.platform.<fn>
"""

import frappe
from frappe import _

from coreerp.platform.extensions import get_extensions
from coreerp.organization.tenant import get_allowed_organizations, get_default_organization


@frappe.whitelist()
def whoami():
	"""Identity + tenant context for the current session (handy for SPA bootstrap)."""
	user = frappe.session.user
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name"),
		"roles": frappe.get_roles(user),
		"organizations": get_allowed_organizations(user),
		"default_organization": get_default_organization(user),
	}


@frappe.whitelist()
def list_modules():
	"""The CoreERP module map — useful for building a dynamic navigation."""
	return frappe.get_all(
		"Module Def",
		filters={"app_name": "coreerp"},
		fields=["name as module", "name as label"],
		order_by="name",
	)


@frappe.whitelist()
def platform_summary():
	"""Counts across the core business doctypes for a landing dashboard."""
	doctypes = ["Client", "Vendor", "Project", "Task", "Ticket", "Lead", "Opportunity"]
	summary = {}
	for dt in doctypes:
		if frappe.has_permission(dt, "read"):
			summary[dt] = frappe.db.count(dt)
	# Allow plugins to contribute extra summary entries.
	for contribution in get_extensions("api_namespaces"):
		if isinstance(contribution, dict):
			summary.update(contribution)
	return summary
