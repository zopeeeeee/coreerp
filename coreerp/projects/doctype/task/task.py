# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Task(Document):
	def validate(self):
		if self.exp_start_date and self.exp_end_date:
			if getdate(self.exp_end_date) < getdate(self.exp_start_date):
				frappe.throw(_("Expected End Date cannot be before Expected Start Date."))
		if self.status == "Completed":
			self.progress = 100


def update_project_progress(doc, method=None):
	"""Doc-event target (hooks.py doc_events['Task']['on_update']).

	Roll the task's completion up into its Project's percent_complete.
	"""
	if not doc.project:
		return
	project = frappe.get_doc("Project", doc.project)
	project.update_percent_complete()
	project.db_set("percent_complete", project.percent_complete, update_modified=False)


def mark_overdue_tasks():
	"""Scheduler target (hooks.py scheduler_events['daily'])."""
	overdue = frappe.get_all(
		"Task",
		filters={
			"status": ["in", ["Open", "Working", "Pending Review"]],
			"exp_end_date": ["<", nowdate()],
		},
		pluck="name",
	)
	for name in overdue:
		frappe.db.set_value("Task", name, "priority", "High", update_modified=False)
	if overdue:
		frappe.db.commit()
