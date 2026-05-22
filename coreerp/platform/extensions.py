"""
CoreERP Extension Registry — the plugin backbone.

This is the public contract downstream apps (university_erp, hospital_erp, crm_pro,
supportdesk, a finance plugin, …) use to plug into CoreERP WITHOUT forking it.

Two complementary mechanisms:

1. App hooks (preferred, declarative). Any installed app may expose, in its own
   hooks.py, a `coreerp_extensions` dict. CoreERP discovers it via
   frappe.get_hooks("coreerp_extensions"). Example in a downstream app's hooks.py:

       coreerp_extensions = {
           "party_dashboards":  ["university_erp.extend.client_dashboard"],
           "workspace_shortcuts": ["university_erp.extend.workspace_shortcuts"],
           "tenant_doctypes":   ["Admission", "Course Enrollment"],
       }

2. Runtime registration (imperative). For dynamic cases, call register() from your
   app's after_install or boot.

CoreERP itself consumes these registries at well-defined extension points (party
dashboards, workspace injection, tenant-scoped doctype list, role bundles, portal
items, API namespaces). See docs/plugin-development-guide.md.
"""

from collections import defaultdict

import frappe

# Recognized extension kinds. Downstream apps should use these keys.
EXTENSION_KINDS = {
	"party_dashboards",      # add cards/links to Client/Vendor dashboards
	"tenant_doctypes",       # doctypes that should be tenant-scoped (get org filter)
	"workspace_shortcuts",   # inject shortcuts into the CoreERP workspace
	"portal_items",          # add portal menu items
	"role_bundles",          # contribute roles to a role profile
	"api_namespaces",        # register a whitelisted API namespace
	"setup_steps",           # add steps to the setup wizard
}

# In-process runtime registry (augments hook-based discovery).
_runtime_registry: dict[str, list] = defaultdict(list)


def register(kind: str, value) -> None:
	"""Imperatively register an extension at runtime."""
	if kind not in EXTENSION_KINDS:
		frappe.throw(f"Unknown CoreERP extension kind: {kind}")
	_runtime_registry[kind].append(value)


def get_extensions(kind: str) -> list:
	"""Return all contributions for a kind, merged from app hooks + runtime registry.

	App-hook values are method paths or literals declared under `coreerp_extensions`
	in any installed app's hooks.py. Results are de-duplicated, order-preserving.
	"""
	if kind not in EXTENSION_KINDS:
		frappe.throw(f"Unknown CoreERP extension kind: {kind}")

	merged: list = []
	hook_map = frappe.get_hooks("coreerp_extensions") or {}
	# frappe.get_hooks returns a dict-of-lists when the hook value is a dict.
	for value in _as_list(hook_map.get(kind)):
		if value not in merged:
			merged.append(value)
	for value in _runtime_registry.get(kind, []):
		if value not in merged:
			merged.append(value)
	return merged


def run_extensions(kind: str, *args, **kwargs) -> list:
	"""Resolve each contribution as a callable (dotted path) and invoke it.

	Non-callable literals (e.g. doctype names under `tenant_doctypes`) are returned
	as-is. Callables receive *args/**kwargs and their return value is collected.
	"""
	results = []
	for value in get_extensions(kind):
		if isinstance(value, str) and "." in value and _looks_like_method(value):
			try:
				results.append(frappe.get_attr(value)(*args, **kwargs))
			except Exception:
				frappe.log_error(title=f"CoreERP extension failed: {value}")
		else:
			results.append(value)
	return results


def get_tenant_doctypes() -> list[str]:
	"""All doctypes that should participate in row-level tenant isolation.

	The universal core scopes only its own Organization-aware doctypes; downstream
	apps contribute theirs via the `tenant_doctypes` extension (in their hooks.py
	`coreerp_extensions`).
	"""
	base = ["Employee Profile", "Holiday List"]
	for extra in get_extensions("tenant_doctypes"):
		if extra not in base:
			base.append(extra)
	return base


def _as_list(value) -> list:
	if value is None:
		return []
	return value if isinstance(value, list) else [value]


def _looks_like_method(dotted: str) -> bool:
	# Heuristic: a method path's last segment is a function name, not a doctype label.
	return dotted.split(".")[-1].islower() or "_" in dotted.split(".")[-1]
