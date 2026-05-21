# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
Runtime smoke test for CoreERP. Run standalone (bench execute can't import coreerp.*):
    cd frappe-bench/sites && ../env/bin/python -c "import frappe; frappe.init(site='S'); \
        frappe.connect(); import coreerp.tests.smoke as s; s.run()"

Exercises CRUD + every hooked doc_event + scheduler entrypoints + tenant query + perms,
so a single run proves the platform works end to end. Run on a throwaway verify site.
"""

import frappe


def _p(results, cond, msg):
	results.append(("PASS" if cond else "FAIL", msg))


def run():
	frappe.set_user("Administrator")
	r = []
	org = "My Organization"

	# ---- CRUD: Client (autonamed by series, so capture real name) ----
	client = _get_or_create("Client", {"client_name": "Acme Corp"}, {"organization": org})
	_p(r, frappe.db.exists("Client", client), f"Client created: {client}")

	# ---- Project + Task rollup (doc_event: task.update_project_progress) ----
	proj = _get_or_create("Project", {"project_name": "Website Revamp"},
	                      {"organization": org, "client": client})
	_get_or_create("Task", {"subject": "Design", "project": proj}, {"status": "Completed"})
	_get_or_create("Task", {"subject": "Build", "project": proj}, {"status": "Open"})
	t = frappe.get_doc("Task", {"subject": "Design", "project": proj})
	t.save()
	pct = frappe.db.get_value("Project", proj, "percent_complete")
	_p(r, pct == 50.0, f"Project % rollup = {pct} (expect 50.0)")
	torg = frappe.db.get_value("Task", {"subject": "Design", "project": proj}, "organization")
	_p(r, torg == org, f"Task fetch_from organization = {torg}")

	# ---- Ticket SLA (doc_event: ticket.apply_sla) ----
	if not frappe.db.exists("Ticket Priority", "High"):
		frappe.get_doc({"doctype": "Ticket Priority", "ticket_priority": "High"}).insert()
	if not frappe.db.exists("Service Level Agreement", "Standard"):
		frappe.get_doc({
			"doctype": "Service Level Agreement", "sla_name": "Standard", "is_default": 1,
			"priorities": [{"priority": "High", "response_time": 3600,
			                "resolution_time": 14400, "default_priority": 1}],
		}).insert()
	tk = frappe.get_doc({"doctype": "Ticket", "subject": "Cannot login", "priority": "High",
	                     "client": client, "organization": org}).insert()
	tk.reload()
	_p(r, bool(tk.response_by and tk.resolution_by),
	   f"Ticket SLA applied: response_by={tk.response_by}, resolution_by={tk.resolution_by}")

	# ---- Timesheet hours (doc_event: timesheet.calculate_hours) ----
	emp = _get_or_create("Employee Profile", {"employee_name": "Jane Doe"}, {"organization": org})
	ts = frappe.get_doc({"doctype": "Timesheet", "employee": emp, "organization": org,
	                     "time_logs": [{"from_time": "2026-05-21 09:00:00",
	                                    "to_time": "2026-05-21 12:30:00"}]}).insert()
	ts.reload()
	_p(r, ts.total_hours == 3.5, f"Timesheet total_hours = {ts.total_hours} (expect 3.5)")

	# ---- Lead convert (whitelisted method) ----
	lead = frappe.get_doc({"doctype": "Lead", "lead_name": "Bob", "company_name": "Beta LLC",
	                       "status": "Qualified"}).insert()
	new_client = lead.convert_to_client()
	lead.reload()
	_p(r, lead.status == "Converted" and frappe.db.exists("Client", new_client),
	   f"Lead -> Client {new_client}, status={lead.status}")

	# ---- Scheduler entrypoints callable ----
	from coreerp.engagement.doctype.opportunity.opportunity import auto_close_stale_opportunities
	from coreerp.projects.doctype.task.task import mark_overdue_tasks
	from coreerp.service.doctype.service_level_agreement.service_level_agreement import check_breaches
	from coreerp.service.doctype.ticket.ticket import auto_close_resolved_tickets
	try:
		auto_close_resolved_tickets(); mark_overdue_tasks()
		auto_close_stale_opportunities(); check_breaches()
		_p(r, True, "All 4 scheduler jobs ran without error")
	except Exception as e:
		_p(r, False, f"Scheduler job error: {e}")

	# ---- Tenant query + extension registry ----
	from coreerp.organization.tenant import get_permission_query_conditions
	from coreerp.platform.extensions import get_tenant_doctypes
	_p(r, get_permission_query_conditions("Administrator") == "",
	   "Tenant filter bypassed for Administrator (empty condition)")
	_p(r, "Client" in get_tenant_doctypes() and len(get_tenant_doctypes()) >= 8,
	   f"Tenant doctypes registered: {len(get_tenant_doctypes())}")

	# ---- API ----
	from coreerp.api.platform import platform_summary, whoami
	_p(r, whoami().get("user") == "Administrator", "API whoami user=Administrator")
	_p(r, "Client" in platform_summary(), f"API platform_summary keys={list(platform_summary().keys())}")

	# ---- Permissions: a restricted role cannot write a doctype it lacks ----
	_test_permissions(r, org)

	# ---- Tenant isolation with a real User Permission ----
	_test_tenant_isolation(r, org)

	frappe.set_user("Administrator")
	frappe.db.commit()

	passed = sum(1 for s, _ in r if s == "PASS")
	for status, msg in r:
		print(f"  [{status}] {msg}")
	print(f"\n  RESULT: {passed}/{len(r)} checks passed")
	if passed != len(r):
		raise Exception(f"{len(r) - passed} smoke checks FAILED")
	return "ALL PASS"


def _test_permissions(r, org):
	"""A Service Agent should be able to read Ticket but NOT create an Organization."""
	user = _ensure_user("agent@coreerp.test", ["Service Agent"])
	frappe.set_user(user)
	can_read_ticket = frappe.has_permission("Ticket", "read")
	can_create_org = frappe.has_permission("Organization", "create")
	frappe.set_user("Administrator")
	_p(r, can_read_ticket and not can_create_org,
	   f"Perms: Service Agent read Ticket={can_read_ticket}, create Organization={can_create_org} (want True/False)")


def _test_tenant_isolation(r, org):
	"""User restricted to a second org must not see first-org Clients via query conditions."""
	org2 = _get_or_create("Organization", {"organization_name": "Beta Org"}, {"abbr": "BO"})
	# a client in each org
	_get_or_create("Client", {"client_name": "Acme Corp"}, {"organization": org})
	_get_or_create("Client", {"client_name": "Beta Client"}, {"organization": org2})
	user = _ensure_user("tenant@coreerp.test", ["CRM Manager"])  # CRM Manager can read Client
	# restrict the user to org2 only
	if not frappe.db.exists("User Permission", {"user": user, "allow": "Organization", "for_value": org2}):
		frappe.get_doc({"doctype": "User Permission", "user": user,
		                "allow": "Organization", "for_value": org2,
		                "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.set_user(user)
	# get_list APPLIES permission_query_conditions (get_all bypasses them).
	visible = [c.organization for c in frappe.get_list("Client", fields=["organization"])]
	frappe.set_user("Administrator")
	only_org2 = all(o == org2 for o in visible) and len(visible) >= 1
	_p(r, only_org2, f"Tenant isolation: user sees only {set(visible)} (restricted to {org2})")


def _ensure_user(email, roles):
	if not frappe.db.exists("User", email):
		u = frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0],
		                    "send_welcome_email": 0, "roles": [{"role": x} for x in roles]})
		u.insert(ignore_permissions=True)
	return email


def _get_or_create(doctype, key, extra=None):
	existing = frappe.db.exists(doctype, key)
	if existing:
		return existing if isinstance(existing, str) else existing[0]
	doc = frappe.get_doc({"doctype": doctype, **key, **(extra or {})}).insert()
	return doc.name
