# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class Organization(NestedSet):
	"""Neutral tenant / business-unit root.

	This is CoreERP's clean replacement for ERPNext's `Company`. It carries NO
	accounting defaults (no receivable/payable/inventory accounts, no cost centers,
	no warehouses). A finance plugin may add such fields later via Custom Field —
	CoreERP stays neutral.
	"""

	nsm_parent_field = "parent_organization"

	def autoname(self):
		# Named by organization_name (naming_rule: By fieldname).
		self.name = self.organization_name

	def validate(self):
		self._set_abbr()
		self._validate_parent()

	def _set_abbr(self):
		if not self.abbr and self.organization_name:
			self.abbr = "".join(w[0] for w in self.organization_name.split() if w)[:5].upper()

	def _validate_parent(self):
		if self.parent_organization and self.parent_organization == self.name:
			frappe.throw(_("An organization cannot be its own parent."))

	def on_update(self):
		super().on_update()  # maintains nested-set tree

	def on_trash(self):
		super().on_trash()


@frappe.whitelist()
def get_children(doctype=None, parent=None, **kwargs):
	"""Tree view data source for the Organization tree."""
	parent = parent or ""
	return frappe.get_all(
		"Organization",
		filters={"parent_organization": parent} if parent else {"parent_organization": ["in", ["", None]]},
		fields=["name as value", "is_group as expandable", "organization_name as title"],
		order_by="organization_name",
	)
