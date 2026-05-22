# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""notification_config hook — desk notification counters for CoreERP doctypes.

The universal core has no transactional doctypes to count by default. Downstream apps
add their own `notification_config` (Frappe merges across apps).
"""


def get_notification_config():
	return {
		"for_doctype": {},
	}
