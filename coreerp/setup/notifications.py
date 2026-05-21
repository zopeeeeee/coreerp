# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""notification_config hook — desk notification counters for CoreERP doctypes."""


def get_notification_config():
	return {
		"for_doctype": {
			"Ticket": {"status": ["in", ["Open", "Replied"]]},
			"Task": {"status": ["in", ["Open", "Working"]]},
			"Lead": {"status": "Open"},
			"Opportunity": {"status": "Open"},
		},
	}
