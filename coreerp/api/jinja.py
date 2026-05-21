# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""Jinja helpers exposed to print formats / web pages (hooks.py `jinja.methods`)."""

import frappe


def get_organization(name=None):
	"""Return an Organization doc (the current user's default if name omitted)."""
	from coreerp.organization.tenant import get_default_organization

	name = name or get_default_organization()
	if not name:
		return frappe._dict()
	return frappe.get_cached_doc("Organization", name)
