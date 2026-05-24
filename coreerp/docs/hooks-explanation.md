# CoreERP — hooks.py Explained

Every hook CoreERP registers, why it exists, and the anti-coupling rules it follows.
Source: `coreerp/hooks.py`.

## Design rules (the contract)
1. **Depend only on frappe.** `required_apps = ["frappe"]`. Never import erpnext.
2. **No `doc_events["*"]`.** ERPNext's global validate hook is the #1 coupling source; CoreERP
   scopes every event to a named doctype.
3. **No domain-finance scheduler jobs.** Only business-neutral periodic tasks.
4. **Cross-cutting behavior → extension registry**, not baked-in hardcoded references.

## App metadata & assets
`app_name`, `app_title`, `app_publisher`, `app_license = "MIT"`, `app_include_css`.

## Install / boot
| Hook | Function | Purpose |
|---|---|---|
| `after_install` | `setup.install.after_install` | One-time baseline setup |
| `after_migrate` | `setup.install.after_migrate` | Idempotent invariant re-assert |
| `boot_session` | `setup.boot.boot_session` | Inject org context into desk boot |
| `notification_config` | `setup.notifications.get_notification_config` | Desk notification counters |
| `setup_wizard_stages` | `setup.setup_wizard.get_setup_stages` | Minimal neutral wizard |

## fixtures
Versioned config shipped with the app, **filtered** so only CoreERP's own records export:
Roles, Role Profiles, CoreERP Workflows, Custom Fields/Property Setters with `module = CoreERP`.

## doc_events (SCOPED)
```python
"Ticket":    validate→apply_sla,  on_update→update_response_times
"Task":      on_update→update_project_progress
"Timesheet": validate→calculate_hours
"Project":   validate→validate_dates
```
There is intentionally **no `"*"` key**. `scripts/validate.py` fails the build if one is added.

## permission_query_conditions / has_permission
All 8 tenant-scoped doctypes (Client, Vendor, Project, Task, Ticket, Lead, Opportunity, Timesheet)
route through `organization/tenant.py`, so list/report/REST share one tenant rule.

## scheduler_events
```
daily : auto_close_resolved_tickets, auto_close_stale_opportunities, mark_overdue_tasks
hourly: check_breaches (SLA)
```
No `bom_update_log`, `repost_item_valuation`, `depreciation`, `reorder_item` — by design.

## website / portal
`website_route_rules`: `/projects`, `/tickets` only.
`standard_portal_menu_items`: Projects, Tickets for the **Portal Client** role.
`has_website_permission`: tenant-aware portal visibility.

## calendars / global_search / jinja
`calendars = [Task, Holiday List]`; global search over the 8 business doctypes;
`jinja.methods = [coreerp.api.jinja.get_organization]`.

## Extending hooks from a downstream app
Don't edit CoreERP's hooks. In your app's hooks.py add scoped `doc_events`, your own
`scheduler_events`, and a `coreerp_extensions` dict (see `plugin-development-guide.md`).
Frappe merges hooks across installed apps automatically.
