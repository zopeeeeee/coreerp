<div align="center">

# CoreERP

**ERP Foundation Framework** — a reusable, industry-agnostic business platform built on
[Frappe](https://frappeframework.com).

*"Django + ERP foundation" — not "ERPNext minus manufacturing".*

</div>

---

## What is CoreERP?

CoreERP is a clean base layer for building business applications on Frappe **without** dragging in
manufacturing, stock, accounting, or any industry-specific assumptions. It gives you the generic
business primitives every product needs — organizations/tenants, clients, vendors, people, projects,
tasks, leads, opportunities, tickets, SLAs — and leans on Frappe for everything else (auth, RBAC,
workflow, portal, web forms, REST API, notifications, files, dashboards, reports, print, jobs).

Build on top of it:

- SaaS products · Custom ERPs · University ERP · CRM · HRMS
- Ticketing / helpdesk · Client portals · Workflow systems
- Project & consulting platforms · Internal tools · Service businesses

## What CoreERP deliberately EXCLUDES

❌ Manufacturing (BOM, Work Order, Routing, Job Card, MRP, Workstation)
❌ Stock / inventory valuation · ❌ Accounting / GL / ledgers
❌ Supply-chain coupling · ❌ Country-specific tax/regional logic · ❌ Industry verticals

These are **opt-in plugins/apps** you install on top of CoreERP when (and only when) you need them.

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

## Modules

| Module | Doctypes |
|---|---|
| Organization | Organization (tenant root) |
| Parties | Client, Vendor, Client Group, Vendor Group, Party Type |
| Common | UOM, UOM Conversion Factor, Territory, Brand, Terms and Conditions |
| HR Basics | Department, Designation, Branch, Employee Profile, Holiday List, Holiday |
| Engagement | Lead, Opportunity, Campaign, Lead Source, Market Segment |
| Projects | Project, Task, Timesheet, Project Type, Task Type, Activity Type |
| Service | Ticket, Service Level Agreement, Ticket Priority, Ticket Type |

## Documentation

See [`coreerp/docs/`](coreerp/docs/):
architecture · dependency-map · app-loading-flow · hooks-explanation ·
doctype-classification · plugin-development-guide · migration-guide ·
how-to-create-new-module · RBAC-guide · portal-system-guide.

## License

MIT — see [license.txt](license.txt). (CoreERP doctypes are authored fresh, not copied from
GPL-licensed ERPNext.)
