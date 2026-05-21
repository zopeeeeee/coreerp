# Copyright (c) 2026, CoreERP Contributors and contributors
# For license information, please see license.txt
"""Patch: ensure CoreERP roles + role profiles exist (idempotent)."""

from coreerp.setup.install import create_role_profiles, create_roles


def execute():
	create_roles()
	create_role_profiles()
