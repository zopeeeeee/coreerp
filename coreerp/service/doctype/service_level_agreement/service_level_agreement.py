# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime


class ServiceLevelAgreement(Document):
	def validate(self):
		self._ensure_single_default()
		self._ensure_single_default_priority()

	def _ensure_single_default(self):
		if self.is_default:
			others = frappe.get_all(
				"Service Level Agreement",
				filters={"is_default": 1, "name": ["!=", self.name]},
				pluck="name",
			)
			for name in others:
				frappe.db.set_value("Service Level Agreement", name, "is_default", 0)

	def _ensure_single_default_priority(self):
		defaults = [p for p in self.priorities if p.default_priority]
		if len(defaults) > 1:
			frappe.throw(_("Only one priority row can be marked as Default Priority."))


def check_breaches():
	"""Scheduler target (hooks.py scheduler_events['hourly']).

	Flag tickets whose resolution deadline has passed without resolution.
	"""
	now = now_datetime()
	open_tickets = frappe.get_all(
		"Ticket",
		filters={
			"status": ["in", ["Open", "Replied", "On Hold"]],
			"agreement_status": "Ongoing",
			"resolution_by": ["is", "set"],
		},
		fields=["name", "resolution_by"],
	)
	breached = [t.name for t in open_tickets if t.resolution_by and get_datetime(t.resolution_by) < now]
	for name in breached:
		frappe.db.set_value("Ticket", name, "agreement_status", "Failed", update_modified=False)
	if breached:
		frappe.db.commit()
