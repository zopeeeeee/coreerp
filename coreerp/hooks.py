"""
CoreERP — ERP Foundation Framework hooks.

DESIGN CONTRACT (read before editing):
  1. CoreERP depends ONLY on `frappe`. It must never import from `erpnext`.
  2. NEVER register a `doc_events["*"]` global validate. Scope every event to a
     specific doctype. (This is the single biggest source of coupling in ERPNext —
     see PLATFORM-ANALYSIS/04-manufacturing-removal-plan.md.)
  3. No manufacturing / stock / accounting scheduler jobs.
  4. Masters are pure data; cross-cutting behavior lives behind the extension
     registry (coreerp/core/extensions.py), so downstream apps plug in without
     forking CoreERP.
"""

app_name = "coreerp"
app_title = "CoreERP"
app_publisher = "CoreERP Contributors"
app_description = "ERP Foundation Framework — reusable, industry-agnostic business platform on Frappe"
app_email = "dev@coreerp.local"
app_license = "MIT"
app_logo_url = "/assets/coreerp/images/coreerp-logo.svg"
required_apps = ["frappe"]

develop_version = "0.x.x-develop"

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
app_include_css = "coreerp.bundle.css"
# app_include_js = "coreerp.bundle.js"   # enable when bundle is added

# ---------------------------------------------------------------------------
# Install / boot
# ---------------------------------------------------------------------------
after_install = "coreerp.setup.install.after_install"
after_migrate = "coreerp.setup.install.after_migrate"
boot_session = "coreerp.setup.boot.boot_session"
notification_config = "coreerp.setup.notifications.get_notification_config"

setup_wizard_stages = "coreerp.setup.setup_wizard.get_setup_stages"

# ---------------------------------------------------------------------------
# Fixtures — versioned platform configuration shipped with the app.
# Filtered so we only export CoreERP's own records, never the whole site.
# ---------------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "Organization Manager",
        "Platform Admin",
        "CRM User",
        "CRM Manager",
        "Project Manager",
        "Project Member",
        "Service Agent",
        "Service Manager",
        "HR Basic User",
        "Portal Client",
    ]]]},
    {"dt": "Role Profile", "filters": [["name", "in", [
        "CoreERP Admin",
        "CoreERP CRM",
        "CoreERP Projects",
        "CoreERP Service",
    ]]]},
    {"dt": "Workflow", "filters": [["name", "like", "CoreERP%"]]},
    {"dt": "Custom Field", "filters": [["module", "=", "Core"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Core"]]},
]

# ---------------------------------------------------------------------------
# Document events — SCOPED ONLY. There is intentionally NO "*" entry.
# ---------------------------------------------------------------------------
doc_events = {
    "Ticket": {
        "validate": "coreerp.service.doctype.ticket.ticket.apply_sla",
        "on_update": "coreerp.service.doctype.ticket.ticket.update_response_times",
    },
    "Task": {
        "on_update": "coreerp.projects.doctype.task.task.update_project_progress",
    },
    "Timesheet": {
        "validate": "coreerp.projects.doctype.timesheet.timesheet.calculate_hours",
    },
    "Project": {
        "validate": "coreerp.projects.doctype.project.project.validate_dates",
    },
}

# ---------------------------------------------------------------------------
# Permission query conditions — tenant isolation enforced at the query layer.
# Every tenant-scoped doctype routes through one shared condition builder.
# ---------------------------------------------------------------------------
permission_query_conditions = {
    "Client": "coreerp.organization.tenant.get_permission_query_conditions",
    "Vendor": "coreerp.organization.tenant.get_permission_query_conditions",
    "Project": "coreerp.organization.tenant.get_permission_query_conditions",
    "Task": "coreerp.organization.tenant.get_permission_query_conditions",
    "Ticket": "coreerp.organization.tenant.get_permission_query_conditions",
    "Lead": "coreerp.organization.tenant.get_permission_query_conditions",
    "Opportunity": "coreerp.organization.tenant.get_permission_query_conditions",
    "Timesheet": "coreerp.organization.tenant.get_permission_query_conditions",
}

has_permission = {
    "Client": "coreerp.organization.tenant.has_permission",
    "Vendor": "coreerp.organization.tenant.has_permission",
    "Project": "coreerp.organization.tenant.has_permission",
    "Ticket": "coreerp.organization.tenant.has_permission",
}

# ---------------------------------------------------------------------------
# Scheduler — only platform-generic, business-neutral jobs.
# (No bom_update_log, no repost_item_valuation, no depreciation — by design.)
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "coreerp.service.doctype.ticket.ticket.auto_close_resolved_tickets",
        "coreerp.engagement.doctype.opportunity.opportunity.auto_close_stale_opportunities",
        "coreerp.projects.doctype.task.task.mark_overdue_tasks",
    ],
    "hourly": [
        "coreerp.service.doctype.service_level_agreement.service_level_agreement.check_breaches",
    ],
}

# ---------------------------------------------------------------------------
# Website / portal — CoreERP registers its OWN generic routes only.
# No /orders, /invoices, /boms, etc. Downstream apps add their own.
# ---------------------------------------------------------------------------
website_route_rules = [
    {"from_route": "/projects", "to_route": "Project"},
    {"from_route": "/tickets", "to_route": "Ticket"},
]

standard_portal_menu_items = [
    {"title": "Projects", "route": "/projects", "reference_doctype": "Project", "role": "Portal Client"},
    {"title": "Tickets", "route": "/tickets", "reference_doctype": "Ticket", "role": "Portal Client"},
]

has_website_permission = {
    "Project": "coreerp.organization.tenant.has_website_permission",
    "Ticket": "coreerp.organization.tenant.has_website_permission",
}

# ---------------------------------------------------------------------------
# Calendars / global search — generic doctypes only.
# ---------------------------------------------------------------------------
calendars = ["Task", "Holiday List"]

global_search_doctypes = {
    "Default": [
        {"doctype": "Client", "index": 0},
        {"doctype": "Vendor", "index": 1},
        {"doctype": "Project", "index": 2},
        {"doctype": "Task", "index": 3},
        {"doctype": "Ticket", "index": 4},
        {"doctype": "Lead", "index": 5},
        {"doctype": "Opportunity", "index": 6},
        {"doctype": "Employee Profile", "index": 7},
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

# ---------------------------------------------------------------------------
# These docs link to many things; don't block deletion on back-links.
# ---------------------------------------------------------------------------
ignore_links_on_delete = []
