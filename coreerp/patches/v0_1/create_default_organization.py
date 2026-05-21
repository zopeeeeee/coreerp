# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""Patch: ensure a default Organization + Party Types + Settings exist (idempotent)."""

from coreerp.setup.install import (
	create_default_organization,
	create_default_party_types,
	ensure_settings,
)


def execute():
	create_default_party_types()
	create_default_organization()
	ensure_settings()
