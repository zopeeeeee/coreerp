# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
Install / migrate orchestration (hooks.py `after_install`, `after_migrate`).

after_install runs once on `bench install-app coreerp` and produces the clean
"baseline mode" platform: roles, role profiles, a default Organization, party types,
portal defaults, and the CoreERP Settings single.
"""

import frappe

# Roles shipped by CoreERP. (Also exported as a fixture; created here so a fresh
# install is usable even before fixtures sync.)
COREERP_ROLES = [
	"Organization Manager",
	"Platform Admin",
	"CRM User",
	"CRM Manager",
	"Project Manager",
	"Project Member",
	"Service Agent",
	"Service Manager",
	"HR Basic User",
	"Portal Client",
]

ROLE_PROFILES = {
	"CoreERP Admin": ["Organization Manager", "Platform Admin", "CRM Manager",
	                  "Project Manager", "Service Manager", "HR Basic User"],
	"CoreERP CRM": ["CRM Manager", "CRM User"],
	"CoreERP Projects": ["Project Manager", "Project Member"],
	"CoreERP Service": ["Service Manager", "Service Agent"],
}

DEFAULT_PARTY_TYPES = ["Client", "Vendor"]


def after_install():
	create_roles()
	create_role_profiles()
	create_default_party_types()
	create_default_organization()
	ensure_settings()
	setup_portal_defaults()
	frappe.db.commit()
	print("CoreERP: baseline platform installed.")


def after_migrate():
	# Idempotent: keep platform invariants intact on every migrate.
	create_roles()
	ensure_settings()
	frappe.db.commit()


# ---------------------------------------------------------------------------
# Building blocks (each idempotent)
# ---------------------------------------------------------------------------
def create_roles():
	for role in COREERP_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"desk_access": 0 if role == "Portal Client" else 1,
			}).insert(ignore_permissions=True)


def create_role_profiles():
	for profile, roles in ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", profile):
			continue
		frappe.get_doc({
			"doctype": "Role Profile",
			"role_profile": profile,
			"roles": [{"role": r} for r in roles],
		}).insert(ignore_permissions=True)


def create_default_party_types():
	for pt in DEFAULT_PARTY_TYPES:
		if not frappe.db.exists("Party Type", pt):
			frappe.get_doc({"doctype": "Party Type", "party_type": pt}).insert(ignore_permissions=True)


def create_default_organization():
	if frappe.db.count("Organization"):
		return
	frappe.get_doc({
		"doctype": "Organization",
		"organization_name": "My Organization",
		"abbr": "MO",
		"default_currency": "USD",
	}).insert(ignore_permissions=True)


def ensure_settings():
	if not frappe.db.exists("Singles", {"doctype": "CoreERP Settings"}):
		settings = frappe.get_single("CoreERP Settings")
		default_org = frappe.db.get_value("Organization", {}, "name")
		if default_org:
			settings.default_organization = default_org
		settings.flags.ignore_permissions = True
		settings.save(ignore_permissions=True)


def setup_portal_defaults():
	portal = frappe.get_single("Portal Settings")
	portal.default_role = "Portal Client"
	portal.flags.ignore_permissions = True
	try:
		portal.save(ignore_permissions=True)
	except Exception:
		# Portal Settings may sync menu from hooks; non-fatal during install.
		frappe.clear_last_message()
