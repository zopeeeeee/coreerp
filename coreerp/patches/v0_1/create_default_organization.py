# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""Patch: ensure a default Organization + Settings exist (idempotent)."""

from coreerp.setup.install import create_default_organization, ensure_settings


def execute():
	create_default_organization()
	ensure_settings()
