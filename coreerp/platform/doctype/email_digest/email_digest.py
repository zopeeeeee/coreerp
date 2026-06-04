# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""
Email Digest — periodic email summarizing site activity.

Pure platform feature: no domain logic, no required doctypes. The list of
"counted doctypes" is configurable per-digest via CSV so the same code serves any
downstream app (university, hospital, internal tool).

Wired to the scheduler via send_due() — see hooks.py.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, today


class EmailDigest(Document):
	def validate(self):
		if not self.next_send:
			self.next_send = today()
		# de-duplicate recipient emails
		seen = set()
		kept = []
		for row in self.recipients:
			email = (row.recipient or "").strip().lower()
			if email and email not in seen:
				seen.add(email)
				row.recipient = email
				kept.append(row)
		self.recipients = kept

	def build_message(self) -> str:
		"""Compose the digest body — header + counts table + footer."""
		body = [self.header or ""]
		if self.include_open_count and self.doctypes_csv:
			rows = []
			for raw in self.doctypes_csv.split(","):
				dt = raw.strip()
				if not dt or not frappe.db.table_exists(dt):
					continue
				filters = {}
				if self.organization and "organization" in [f.fieldname for f in frappe.get_meta(dt).fields]:
					filters["organization"] = self.organization
				rows.append(f"<tr><td>{dt}</td><td style='text-align:right'>{frappe.db.count(dt, filters)}</td></tr>")
			if rows:
				body.append(
					"<table style='border-collapse:collapse' border='1' cellpadding='6'>"
					"<thead><tr><th>Doctype</th><th>Count</th></tr></thead>"
					f"<tbody>{''.join(rows)}</tbody></table>"
				)
		body.append(self.footer or "")
		return "\n\n".join(p for p in body if p)

	def send_now(self) -> int:
		"""Send the digest to enabled recipients. Returns the count sent."""
		emails = [r.recipient for r in self.recipients if r.enabled and r.recipient]
		if not emails:
			return 0
		frappe.sendmail(
			recipients=emails,
			subject=self.subject or f"CoreERP Digest — {self.name}",
			message=self.build_message(),
			now=False,
		)
		# advance next_send by frequency
		base = getdate(self.next_send or today())
		if self.frequency == "Daily":
			self.next_send = add_days(base, 1)
		elif self.frequency == "Monthly":
			self.next_send = add_months(base, 1)
		else:  # Weekly default
			self.next_send = add_days(base, 7)
		self.db_set("next_send", self.next_send, update_modified=False)
		return len(emails)


def send_due():
	"""Scheduler entry (daily): send each enabled digest whose next_send <= today."""
	due = frappe.get_all(
		"Email Digest",
		filters={"enabled": 1, "next_send": ["<=", today()]},
		pluck="name",
	)
	sent = 0
	for name in due:
		try:
			sent += frappe.get_doc("Email Digest", name).send_now()
		except Exception:
			frappe.log_error(title=f"Email Digest send failed: {name}")
	if due:
		frappe.db.commit()
	return {"digests": len(due), "emails_sent": sent}
