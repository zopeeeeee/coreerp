# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Lead(Document):
	"""De-coupled Lead. ERPNext's Lead inherits `SellingController` and imports
	`erpnext.accounts.party.set_taxes`; CoreERP's Lead is a plain Document with no
	tax/selling coupling.
	"""

	def validate(self):
		if self.email_id:
			self.email_id = self.email_id.strip().lower()

	@frappe.whitelist()
	def convert_to_client(self):
		"""Promote a qualified Lead into a Client (neutral, no accounting)."""
		if self.status == "Converted":
			frappe.throw(_("This lead is already converted."))
		client = frappe.get_doc({
			"doctype": "Client",
			"client_name": self.company_name or self.lead_name,
			"organization": self.organization,
			"territory": self.territory,
			"market_segment": self.market_segment,
			"website": self.website,
		})
		client.insert(ignore_permissions=True)
		self.db_set("status", "Converted")
		return client.name
