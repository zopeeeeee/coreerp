"""
Tenant isolation for CoreERP.

CoreERP supports row-level multi-tenancy via a single `Organization` link on
tenant-scoped doctypes plus Frappe User Permissions. This module centralizes the
enforcement so every scoped doctype shares ONE rule (registered in hooks.py under
`permission_query_conditions` / `has_permission`).

Two tenancy models are supported (see docs/RBAC-guide.md):
  * Model A — site-per-tenant (hard isolation; nothing here needed).
  * Model B — row-level (this module): one Organization per user via User Permission.

A user who is a System Manager / Platform Admin bypasses tenant filtering.
A user with NO Organization user-permission sees everything they otherwise can
(i.e. tenant filtering only narrows; it never grants).
"""

import frappe

# Roles that are never tenant-restricted.
TENANT_BYPASS_ROLES = {"System Manager", "Administrator", "Platform Admin"}

TENANT_FIELD = "organization"


def _user_is_bypassed(user: str) -> bool:
	if user == "Administrator":
		return True
	user_roles = set(frappe.get_roles(user))
	return bool(user_roles & TENANT_BYPASS_ROLES)


def get_allowed_organizations(user: str | None = None) -> list[str]:
	"""Organizations the user is restricted to via User Permission. Empty = unrestricted."""
	user = user or frappe.session.user
	if _user_is_bypassed(user):
		return []
	perms = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Organization"},
		pluck="for_value",
	)
	return perms or []


def get_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""Inject a WHERE clause so list/report/REST all see the same tenant scope.

	Registered for the core's Organization-aware doctypes (Employee Profile, Holiday
	List); downstream apps point their own doctypes at this same function.
	Frappe calls this as ``fn(user, doctype)`` and ANDs the returned string into the
	query, so we return a self-contained, table-qualified clause.

	Note: records with a NULL organization are intentionally HIDDEN from a
	tenant-restricted user — leaving them visible would defeat isolation. Assign an
	organization to every tenant record (or use site-per-tenant for global data).
	"""
	user = user or frappe.session.user
	allowed = get_allowed_organizations(user)
	if not allowed:
		return ""

	quoted = ", ".join(frappe.db.escape(o) for o in allowed)
	# Table-qualify when the doctype is known so the clause is unambiguous even when
	# Frappe joins other tables.
	col = f"`tab{doctype}`.`{TENANT_FIELD}`" if doctype else f"`{TENANT_FIELD}`"
	return f"{col} in ({quoted})"


def has_permission(doc=None, ptype=None, user=None, **kwargs) -> bool:
	"""Document-level tenant check (mirror of the query condition for single-doc access).

	Frappe calls this hook as ``fn(doc=doc, ptype=ptype, user=user)``. During
	doctype-level checks (e.g. building a list query) ``doc`` is None — in that case we
	allow, because row scoping is enforced by ``get_permission_query_conditions``.
	"""
	user = user or frappe.session.user
	if doc is None:
		return True
	allowed = get_allowed_organizations(user)
	if not allowed:
		return True
	org = doc.get(TENANT_FIELD)
	if not org:
		# Unassigned records are hidden from tenant-restricted users (matches query cond).
		return False
	return org in allowed


def has_website_permission(doc, ptype, user, verbose=False) -> bool:
	"""Portal access: a portal client may see records of their own organization."""
	user = user or frappe.session.user
	allowed = get_allowed_organizations(user)
	if not allowed:
		# A portal user with no org restriction should not see everything.
		# Restrict to records they own.
		return doc.get("owner") == user
	return doc.get(TENANT_FIELD) in allowed


def get_default_organization(user: str | None = None) -> str | None:
	"""Return the user's default Organization, else the site's single/first one."""
	user = user or frappe.session.user
	allowed = get_allowed_organizations(user)
	if allowed:
		return allowed[0]
	default = frappe.defaults.get_user_default("organization", user)
	if default:
		return default
	orgs = frappe.get_all("Organization", filters={"is_group": 0}, pluck="name", limit=1)
	return orgs[0] if orgs else None
