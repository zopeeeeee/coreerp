# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document


class Client(Document):
	"""Neutral party master — CoreERP's clean replacement for ERPNext `Customer`.

	Crucially, it carries NO `PartyAccount` child table and makes NO call to
	`erpnext.accounts.party.validate_party_accounts`. A finance plugin can attach
	receivable-account behavior later via Custom Field + the extension registry.
	"""

	def onload(self):
		"""Expose linked Contacts/Addresses in the form sidebar (Frappe-native)."""
		load_address_and_contact(self)

	def validate(self):
		self._sync_primary_contact_fields()

	def _sync_primary_contact_fields(self):
		if self.primary_contact:
			contact = frappe.db.get_value(
				"Contact", self.primary_contact, ["email_id", "mobile_no"], as_dict=True
			)
			if contact:
				self.email_id = contact.email_id
				self.mobile_no = contact.mobile_no


@frappe.whitelist()
def get_dashboard_data(name):
	"""Neutral, finance-free dashboard payload for the Client form."""
	return {
		"fieldname": "client",
		"transactions": [
			{"label": _("Engagement"), "items": ["Opportunity"]},
			{"label": _("Delivery"), "items": ["Project"]},
			{"label": _("Support"), "items": ["Ticket"]},
		],
	}
