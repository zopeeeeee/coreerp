# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class Project(Document):
	"""De-financed project. Unlike ERPNext's Project, there is NO costing/billing
	(`total_billable_amount`, `gross_margin`, `cost_center`, Sales Order link). Pure
	delivery tracking: schedule, team, % complete from tasks.
	"""

	def validate(self):
		validate_dates(self)
		self.update_percent_complete()

	def update_percent_complete(self):
		total = frappe.db.count("Task", {"project": self.name})
		if not total:
			return
		completed = frappe.db.count("Task", {"project": self.name, "status": "Completed"})
		self.percent_complete = flt(completed) / total * 100


def validate_dates(doc, method=None):
	"""Doc-event target (hooks.py doc_events['Project']['validate'])."""
	if doc.expected_start_date and doc.expected_end_date:
		if getdate(doc.expected_end_date) < getdate(doc.expected_start_date):
			frappe.throw(_("Expected End Date cannot be before Expected Start Date."))
