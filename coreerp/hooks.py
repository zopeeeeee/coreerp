"""
CoreERP — Universal business platform on Frappe.

Slim, industry-agnostic core: Organization (tenant), generic masters (UOM, Territory,
Brand, Terms), and HR basics (Department, Designation, Branch, Employee Profile, Holiday
List) — plus a tenant-isolation engine, universal roles, and a plugin extension registry.

DESIGN CONTRACT:
  1. CoreERP depends ONLY on `frappe`. Never import from `erpnext`.
  2. NO domain-specific doctypes (CRM/sales/projects/support) and NO domain roles —
     those belong in downstream apps or optional packs, not the universal core.
  3. NEVER register a `doc_events["*"]` global validate. Scope every event.
  4. Cross-cutting behavior goes through the extension registry
     (coreerp/platform/extensions.py) so downstream apps plug in without forking.
"""

app_name = "coreerp"
app_title = "CoreERP"
app_publisher = "CoreERP Contributors"
app_description = "Universal business platform on Frappe — Organization, tenancy, masters, HR basics"
app_email = "dev@coreerp.local"
app_license = "MIT"
app_logo_url = "/assets/coreerp/images/coreerp-logo.svg"
required_apps = ["frappe"]

develop_version = "0.x.x-develop"

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
app_include_css = "coreerp.bundle.css"

# ---------------------------------------------------------------------------
# Install / boot
# ---------------------------------------------------------------------------
after_install = "coreerp.setup.install.after_install"
after_migrate = "coreerp.setup.install.after_migrate"
boot_session = "coreerp.setup.boot.boot_session"
notification_config = "coreerp.setup.notifications.get_notification_config"

setup_wizard_stages = "coreerp.setup.setup_wizard.get_setup_stages"

# ---------------------------------------------------------------------------
# Fixtures — versioned platform configuration (universal roles only).
# ---------------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "Organization Manager",
        "Platform Admin",
        "HR Basic User",
        "Portal Client",
    ]]]},
    {"dt": "Role Profile", "filters": [["name", "in", [
        "CoreERP Admin",
        "CoreERP HR",
    ]]]},
    {"dt": "Custom Field", "filters": [["module", "=", "Platform"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Platform"]]},
]

# ---------------------------------------------------------------------------
# Document events — SCOPED ONLY. There is intentionally NO "*" entry.
# The slim core ships none; downstream apps add their own scoped events.
# ---------------------------------------------------------------------------
doc_events = {}

# ---------------------------------------------------------------------------
# Tenant isolation — the only doctype the core scopes is Organization-aware HR data.
# Downstream apps register THEIR tenant doctypes via `coreerp_extensions`
# (see coreerp/platform/extensions.py) and point their own
# permission_query_conditions at coreerp.organization.tenant.
# ---------------------------------------------------------------------------
permission_query_conditions = {
    "Employee Profile": "coreerp.organization.tenant.get_permission_query_conditions",
    "Holiday List": "coreerp.organization.tenant.get_permission_query_conditions",
}

has_permission = {
    "Employee Profile": "coreerp.organization.tenant.has_permission",
}

# ---------------------------------------------------------------------------
# Scheduler — the universal core ships no periodic jobs.
# ---------------------------------------------------------------------------
scheduler_events = {}

# ---------------------------------------------------------------------------
# Calendars / global search — universal masters only.
# ---------------------------------------------------------------------------
calendars = ["Holiday List"]

global_search_doctypes = {
    "Default": [
        {"doctype": "Organization", "index": 0},
        {"doctype": "Employee Profile", "index": 1},
        {"doctype": "Department", "index": 2},
    ],
}

# ---------------------------------------------------------------------------
# Jinja — expose CoreERP helpers to print formats / web pages.
# ---------------------------------------------------------------------------
jinja = {
    "methods": [
        "coreerp.api.jinja.get_organization",
    ],
}

ignore_links_on_delete = []
