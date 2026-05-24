<div align="center">

# CoreERP

**ERP Foundation Framework** — a reusable, industry-agnostic business platform built on
[Frappe](https://frappeframework.com).

*"Django + ERP foundation" — not "ERPNext minus manufacturing".*

</div>

---

## What is CoreERP?

CoreERP is a clean base layer for building business applications on Frappe **without** dragging in
manufacturing, stock, accounting, or any industry-specific assumptions. It gives you only the
**truly universal** primitives every business app needs — a tenant/Organization model, row-level
tenant isolation, universal masters (UOM, Territory, Brand, Terms), HR basics (Department,
Designation, Employee Profile, Holiday List), universal roles, and a plugin extension registry —
and leans on Frappe for everything else (auth, RBAC, workflow, portal, web forms, REST API,
notifications, files, dashboards, reports, print, jobs).

Build *your* domain entities on top of it:

- University ERP (Student, Course, Admission) · Hospital ERP (Patient, Encounter)
- Internal tools · Workflow systems · Client portals
- HRMS · Logistics · School/Gym/Library management · any custom enterprise app

## What CoreERP deliberately EXCLUDES

❌ Manufacturing (BOM, Work Order, Routing, MRP) · ❌ Stock / inventory · ❌ Accounting / GL
❌ **CRM/sales** (Client, Vendor, Lead, Opportunity, Campaign) · ❌ **Projects/Timesheet** ·
❌ **Support** (Ticket, SLA) · ❌ Country-specific tax/regional · ❌ Industry verticals

CRM/sales/support are **domain-specific**, not universal — a university or internal tool doesn't
need "Client" or "Ticket". Add such entities in your own app (or an optional pack) only when your
product actually needs them. CoreERP stays a clean, minimal base.

## Architecture

```
your_product_app   (CRM Pro, University ERP, SupportDesk, …)   ← Layer 3
        │ depends on
     coreerp        (this app — generic business platform)     ← Layer 1
        │ depends on
      frappe        (the framework = Universal ERP Core)        ← Layer 0
```

CoreERP `required_apps = ["frappe"]` and **never imports from erpnext**.

## Installation

```bash
# 1. get the app into your bench
bench get-app coreerp /path/to/coreerp        # or a git URL

# 2. create a site (or use an existing one)
bench new-site mysite.localhost

# 3. install
bench --site mysite.localhost install-app coreerp

# 4. open it
bench --site mysite.localhost browse --user Administrator
```

A fresh install gives you a clean platform: default roles, a default Organization, the **CoreERP**
workspace, portal defaults — and **no** ERP menus you didn't ask for.

## Modules (slim universal core — 13 doctypes)

CoreERP ships ONLY what is universal to *any* business app. It deliberately does **not**
include CRM/sales/projects/support doctypes or roles — those are domain-specific and belong
in the apps that need them (add them per-app, or as an optional pack).

| Module | Doctypes |
|---|---|
| Platform | CoreERP Settings (+ extension registry, workspace) |
| Organization | Organization (tenant root) |
| Common | UOM, UOM Conversion Factor, Territory, Brand, Terms and Conditions |
| HR Basics | Department, Designation, Branch, Employee Profile, Holiday List, Holiday |

**Universal roles only:** Organization Manager, Platform Admin, HR Basic User, Portal Client.

What you get on top of Frappe: a tenant/Organization model, a **row-level tenant-isolation
engine** (reusable by your app's doctypes), universal masters, HR basics, universal roles, and
a **plugin extension registry** — without ERPNext's accounting/stock/manufacturing, and without
CRM/sales assumptions.

## Documentation

**Guides** — [`docs/guides/`](docs/guides/):
- [SETUP.md](docs/guides/SETUP.md) — install CoreERP into a bench
- [HOW-TO-RUN.md](docs/guides/HOW-TO-RUN.md) — run/view the verify stack in a browser
- [NEW-APP-PLAYBOOK.md](docs/guides/NEW-APP-PLAYBOOK.md) — build a new app on CoreERP (Frappe Docker → ship). Has a copy-paste Claude Code prompt.
- [MIGRATE-OFF-ERPNEXT.md](docs/guides/MIGRATE-OFF-ERPNEXT.md) — move an existing project off ERPNext onto CoreERP (audit-first, gated, dry-run verified). Has a copy-paste Claude Code prompt.

**Developer reference** — [`coreerp/docs/`](coreerp/docs/):
architecture · plugin-development-guide · RBAC-guide · portal-system-guide ·
hooks-explanation · app-loading-flow · dependency-map · doctype-classification ·
how-to-create-new-module.

**Build tools** — [`scripts/`](scripts/): `validate.py` (static checks), `scaffold.py`
(doctype generator, historical). **Project history** — [`docs/analysis/`](docs/analysis/).

## License

MIT — see [license.txt](license.txt). (CoreERP doctypes are authored fresh, not copied from
GPL-licensed ERPNext.)
