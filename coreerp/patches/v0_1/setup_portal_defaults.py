# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""Patch: set portal defaults (idempotent)."""

from coreerp.setup.install import setup_portal_defaults


def execute():
	setup_portal_defaults()
