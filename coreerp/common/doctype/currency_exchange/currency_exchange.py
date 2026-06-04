# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CurrencyExchange(Document):
	"""Historical FX rate between two currencies on a date.

	Stays generic — no posting, no accounting coupling. A downstream app that needs
	multi-currency conversions can query the most recent rate via `get_rate()`.
	"""

	def validate(self):
		if self.from_currency == self.to_currency:
			frappe.throw(_("From Currency and To Currency must be different."))
		if not self.exchange_rate or self.exchange_rate <= 0:
			frappe.throw(_("Exchange Rate must be greater than zero."))


@frappe.whitelist()
def get_rate(from_currency: str, to_currency: str, date: str | None = None,
             for_buying: int = 1) -> float | None:
	"""Most recent Exchange Rate from `from_currency` to `to_currency` on/before `date`.

	Same currency → 1.0. Returns None if no rate is on file.
	"""
	if from_currency == to_currency:
		return 1.0
	filters = {
		"from_currency": from_currency,
		"to_currency": to_currency,
		"for_buying" if int(for_buying) else "for_selling": 1,
	}
	if date:
		filters["date"] = ["<=", date]
	rows = frappe.get_all(
		"Currency Exchange",
		filters=filters,
		fields=["exchange_rate"],
		order_by="date desc",
		limit=1,
	)
	return rows[0].exchange_rate if rows else None
