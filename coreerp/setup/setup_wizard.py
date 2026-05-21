# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
Setup wizard stages (hooks.py `setup_wizard_stages`).

A deliberately minimal, business-neutral wizard: capture the first Organization and
an admin. No company/accounting/chart-of-accounts steps (the ERPNext wizard's bulk).
Downstream apps can append steps via the `setup_steps` extension kind.
"""

import frappe
from frappe import _


def get_setup_stages(args=None):
	return [
		{
			"status": _("Creating Organization"),
			"fail_msg": _("Could not create Organization"),
			"tasks": [
				{"fn": stage_create_organization, "args": args, "fail_msg": _("Could not create Organization")},
			],
		},
		{
			"status": _("Configuring Platform"),
			"fail_msg": _("Could not configure platform defaults"),
			"tasks": [
				{"fn": stage_configure_defaults, "args": args, "fail_msg": _("Could not set defaults")},
			],
		},
	]


def stage_create_organization(args):
	args = frappe._dict(args or {})
	org_name = args.get("organization_name") or args.get("company_name") or "My Organization"
	if not frappe.db.exists("Organization", org_name):
		frappe.get_doc({
			"doctype": "Organization",
			"organization_name": org_name,
			"default_currency": args.get("currency") or "USD",
			"country": args.get("country") or "United States",
		}).insert(ignore_permissions=True)


def stage_configure_defaults(args):
	args = frappe._dict(args or {})
	settings = frappe.get_single("CoreERP Settings")
	org_name = args.get("organization_name") or args.get("company_name") or "My Organization"
	settings.default_organization = org_name
	settings.default_currency = args.get("currency") or "USD"
	settings.save(ignore_permissions=True)
