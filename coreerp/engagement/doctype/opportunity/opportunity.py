# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, add_to_date, now_datetime, get_datetime


class Opportunity(Document):
	"""De-coupled Opportunity. ERPNext's version inherits `TransactionBase` and pulls
	`erpnext.setup.utils.get_exchange_rate`; CoreERP's is a plain Document. The Items
	table is generic (free-text item/service), not tied to a stock Item master.
	"""

	def validate(self):
		self._compute_item_amounts()

	def _compute_item_amounts(self):
		total = 0.0
		for row in self.items:
			row.amount = flt(row.qty) * flt(row.rate)
			total += row.amount
		if total and not self.opportunity_amount:
			self.opportunity_amount = total


def auto_close_stale_opportunities():
	"""Scheduler target (hooks.py scheduler_events['daily'])."""
	days = frappe.db.get_single_value("CoreERP Settings", "opportunity_stale_days") or 30
	cutoff = add_to_date(now_datetime(), days=-int(days))
	stale = frappe.get_all(
		"Opportunity",
		filters={"status": "Open", "modified": ["<", cutoff]},
		pluck="name",
	)
	for name in stale:
		frappe.db.set_value("Opportunity", name, "status", "Closed", update_modified=False)
	if stale:
		frappe.db.commit()
