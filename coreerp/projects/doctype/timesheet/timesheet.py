# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, time_diff_in_hours


class Timesheet(Document):
	"""De-financed timesheet. No `sales_invoice` link, no billing/costing fields —
	pure time recording. Billing is an optional plugin concern.
	"""

	def validate(self):
		calculate_hours(self)
		self._set_date_range()

	def on_submit(self):
		self.db_set("status", "Submitted")

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	def _set_date_range(self):
		dates = [getdate(d.from_time) for d in self.time_logs if d.from_time]
		if dates:
			self.start_date = min(dates)
			self.end_date = max(dates)


def calculate_hours(doc, method=None):
	"""Doc-event target (hooks.py doc_events['Timesheet']['validate'])."""
	total = 0.0
	for row in doc.time_logs:
		if row.from_time and row.to_time:
			row.hours = flt(time_diff_in_hours(row.to_time, row.from_time), 2)
		total += flt(row.hours)
	doc.total_hours = flt(total, 2)
