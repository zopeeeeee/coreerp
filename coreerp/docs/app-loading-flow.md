# CoreERP — App Loading Flow

How CoreERP boots, installs, and serves — end to end.

## 1. `bench get-app coreerp`
Bench clones the repo into `apps/coreerp`, reads `pyproject.toml`, and pip-installs the package
(editable). `required_apps = ["frappe"]` is recorded.

## 2. `bench --site <site> install-app coreerp`
1. Frappe reads `coreerp/hooks.py` → registers `app_name`, asset bundles, all hook dicts.
2. Frappe reads `coreerp/modules.txt` → creates a **Module Def** per module.
3. Frappe imports every `*/doctype/*/<name>.json` → **creates DB tables** (dependency-ordered).
4. `patches.txt` runs (post-model-sync): `create_default_roles`, `create_default_organization`,
   `setup_portal_defaults`.
5. **`after_install`** (`coreerp/setup/install.py`) runs → roles, role profiles, party types,
   default Organization, CoreERP Settings, portal defaults.
6. **fixtures** sync (roles, role profiles, workflows, custom fields filtered to CoreERP).
7. Result: a clean baseline platform with the **CoreERP** workspace as a landing page.

## 3. `bench migrate` (every deploy)
1. New/changed doctype JSON → schema sync.
2. New `patches.txt` entries run once (tracked in **Patch Log**).
3. **`after_migrate`** re-asserts platform invariants (roles, settings) — idempotent.
4. `fixtures` re-sync. Workspaces rebuilt.

## 4. Request lifecycle (desk)
```
HTTP → frappe.auth (session/API key/OAuth) → permission check (incl. tenant query conditions)
     → controller → response
boot: frappe builds bootinfo → coreerp.setup.boot.boot_session injects frappe.boot.coreerp
```

## 5. Request lifecycle (portal/website)
```
HTTP → frappe.website.path_resolver → route match (website_route_rules: /projects, /tickets)
     → has_website_permission (coreerp.organization.tenant) → render
```

## 6. Background jobs
Frappe scheduler reads `scheduler_events` → enqueues CoreERP jobs (auto-close tickets/opportunities,
mark overdue tasks, SLA breach check) onto RQ. Tracked in **Scheduled Job Type/Log**.

## Boot payload contract
`frappe.boot.coreerp = { default_organization, organizations, tenant_isolation }` —
a SPA/portal frontend can read this immediately after login to scope its UI.
