# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, now_datetime, get_datetime


class Ticket(Document):
	def validate(self):
		if not self.opening_date:
			self.opening_date = now_datetime()
		if self.status in ("Resolved", "Closed") and not self.resolution_date:
			self.resolution_date = now_datetime()


def apply_sla(doc, method=None):
	"""Doc-event target (hooks.py doc_events['Ticket']['validate']).

	Resolve the applicable SLA + set response_by / resolution_by deadlines from the
	matched priority. Pure helpdesk logic — no accounting/stock involved.
	"""
	if doc.response_by and doc.resolution_by:
		return  # already set
	sla_name = doc.service_level_agreement or _default_sla()
	if not sla_name:
		return
	doc.service_level_agreement = sla_name
	sla = frappe.get_cached_doc("Service Level Agreement", sla_name)
	target = _match_priority(sla, doc.priority)
	if not target:
		return
	start = get_datetime(doc.opening_date or now_datetime())
	if target.response_time:
		doc.response_by = add_to_date(start, seconds=target.response_time)
	if target.resolution_time:
		doc.resolution_by = add_to_date(start, seconds=target.resolution_time)


def update_response_times(doc, method=None):
	"""Doc-event target (hooks.py doc_events['Ticket']['on_update'])."""
	if doc.status == "Replied" and not doc.first_responded_on:
		doc.db_set("first_responded_on", now_datetime(), update_modified=False)
	if doc.status in ("Resolved", "Closed"):
		_evaluate_agreement(doc)


def _evaluate_agreement(doc):
	status = "Fulfilled"
	resolved = get_datetime(doc.resolution_date or now_datetime())
	if doc.resolution_by and resolved > get_datetime(doc.resolution_by):
		status = "Failed"
	doc.db_set("agreement_status", status, update_modified=False)


def _default_sla():
	return frappe.db.get_value("Service Level Agreement", {"is_default": 1, "enabled": 1}, "name")


def _match_priority(sla, priority):
	for row in sla.priorities:
		if row.priority == priority:
			return row
	for row in sla.priorities:
		if row.default_priority:
			return row
	return None


def auto_close_resolved_tickets():
	"""Scheduler target (hooks.py scheduler_events['daily'])."""
	days = frappe.db.get_single_value("CoreERP Settings", "auto_close_after_days") or 7
	cutoff = add_to_date(now_datetime(), days=-int(days))
	stale = frappe.get_all(
		"Ticket",
		filters={"status": "Resolved", "resolution_date": ["<", cutoff]},
		pluck="name",
	)
	for name in stale:
		frappe.db.set_value("Ticket", name, {"status": "Closed", "closing_date": now_datetime()},
		                    update_modified=False)
	if stale:
		frappe.db.commit()
