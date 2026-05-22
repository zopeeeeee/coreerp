# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
Runtime smoke test for the slim universal CoreERP. Run standalone:
    cd frappe-bench/sites && ../env/bin/python -c "import frappe; frappe.init(site='S'); \
        frappe.connect(); import coreerp.tests.smoke as s; s.run()"

Covers install artifacts, the universal masters, HR basics, tenant isolation, the
extension registry, and the public API. Run on a throwaway verify site.
"""

import frappe


def _p(results, cond, msg):
	results.append(("PASS" if cond else "FAIL", msg))


def run():
	frappe.set_user("Administrator")
	r = []
	org = "My Organization"

	# 1. Install artifacts: universal roles only (NO CRM/Project/Service roles)
	roles = set(frappe.get_all("Role", pluck="name"))
	want = {"Organization Manager", "Platform Admin", "HR Basic User", "Portal Client"}
	gone = {"CRM Manager", "CRM User", "Project Manager", "Service Agent"}
	_p(r, want <= roles, f"Universal roles present: {sorted(want & roles)}")
	_p(r, not (gone & roles), f"Domain roles absent: {sorted(gone & roles) or 'none'}")

	# 2. Default Organization + Settings
	_p(r, frappe.db.exists("Organization", org), f"Default Organization: {org}")
	_p(r, frappe.db.get_single_value("CoreERP Settings", "default_organization") == org,
	   "CoreERP Settings.default_organization set")

	# 3. Only the 4 universal modules exist
	mods = set(frappe.get_all("Module Def", filters={"app_name": "coreerp"}, pluck="name"))
	_p(r, mods == {"Platform", "Organization", "Common", "HR Basics"},
	   f"Modules = {sorted(mods)}")

	# 4. Removed domain doctypes are truly gone
	for dt in ("Client", "Vendor", "Lead", "Opportunity", "Project", "Task", "Ticket"):
		_p(r, not frappe.db.exists("DocType", dt), f"Removed doctype absent: {dt}")

	# 5. Universal masters work
	uom = _get_or_create("UOM", {"uom_name": "Box"})
	terr = _get_or_create("Territory", {"territory_name": "Global"})
	dept = _get_or_create("Department", {"department_name": "Operations"}, {"organization": org})
	desig = _get_or_create("Designation", {"designation_name": "Manager"})
	_p(r, all([uom, terr, dept, desig]), "Masters create: UOM, Territory, Department, Designation")

	# 6. HR: Employee Profile (org-scoped)
	emp = frappe.get_doc({"doctype": "Employee Profile", "employee_name": "Jane Doe",
	                      "organization": org, "department": dept, "designation": desig}).insert()
	_p(r, frappe.db.exists("Employee Profile", emp.name), f"Employee Profile created: {emp.name}")

	# 7. Tenant isolation engine intact, scoped to HR doctypes
	from coreerp.organization.tenant import get_permission_query_conditions
	from coreerp.platform.extensions import get_tenant_doctypes
	_p(r, get_permission_query_conditions("Administrator") == "",
	   "Tenant filter bypassed for Administrator")
	td = get_tenant_doctypes()
	_p(r, "Employee Profile" in td, f"Tenant doctypes (core) = {td}")

	# 8. Real tenant isolation on Employee Profile via User Permission
	org2 = _get_or_create("Organization", {"organization_name": "Beta Org"}, {"abbr": "BO"})
	frappe.get_doc({"doctype": "Employee Profile", "employee_name": "Bob Beta",
	                "organization": org2}).insert()
	user = _ensure_user("hr@coreerp.test", ["HR Basic User"])
	if not frappe.db.exists("User Permission", {"user": user, "allow": "Organization", "for_value": org2}):
		frappe.get_doc({"doctype": "User Permission", "user": user, "allow": "Organization",
		                "for_value": org2, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.set_user(user)
	visible = [e.organization for e in frappe.get_list("Employee Profile", fields=["organization"])]
	frappe.set_user("Administrator")
	_p(r, visible and all(o == org2 for o in visible),
	   f"Tenant isolation: HR user sees only {set(visible)} (restricted to {org2})")

	# 9. API
	from coreerp.api.platform import platform_summary, whoami
	_p(r, whoami().get("user") == "Administrator", "API whoami works")
	_p(r, "Organization" in platform_summary(), f"API platform_summary keys={list(platform_summary().keys())}")

	frappe.db.commit()
	passed = sum(1 for s, _ in r if s == "PASS")
	for s, m in r:
		print(f"  [{s}] {m}")
	print(f"\n  RESULT: {passed}/{len(r)} checks passed")
	if passed != len(r):
		raise Exception(f"{len(r) - passed} smoke checks FAILED")
	return "ALL PASS"


def _ensure_user(email, roles):
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0],
		                "send_welcome_email": 0, "roles": [{"role": x} for x in roles]}).insert(ignore_permissions=True)
	return email


def _get_or_create(doctype, key, extra=None):
	existing = frappe.db.exists(doctype, key)
	if existing:
		return existing if isinstance(existing, str) else existing[0]
	return frappe.get_doc({"doctype": doctype, **key, **(extra or {})}).insert().name
