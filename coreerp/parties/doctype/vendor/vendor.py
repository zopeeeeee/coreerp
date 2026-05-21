# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document


class Vendor(Document):
	"""Neutral party master — CoreERP's clean replacement for ERPNext `Supplier`.

	No PartyAccount child table, no `erpnext.accounts.party` coupling. Payable-account
	behavior is the concern of an optional finance plugin, not the platform.
	"""

	def onload(self):
		load_address_and_contact(self)

	def validate(self):
		if self.primary_contact:
			contact = frappe.db.get_value(
				"Contact", self.primary_contact, ["email_id", "mobile_no"], as_dict=True
			)
			if contact:
				self.email_id = contact.email_id
				self.mobile_no = contact.mobile_no
