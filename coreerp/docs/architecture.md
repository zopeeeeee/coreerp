# CoreERP — Architecture

CoreERP is a **Frappe app** that provides a clean, industry-agnostic business platform.
It is *not* ERPNext with modules deleted — it is authored fresh, depends only on Frappe,
and never imports from `erpnext`.

## Layering

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3 — Product apps (university_erp, hospital_erp, …)      │
│           depend on coreerp; add their own doctypes/workflows  │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2 — Optional plugins (finance, inventory, billing)      │
│           extend coreerp masters via Custom Field / hooks      │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1 — coreerp  (THIS APP — slim universal core)          │
│           Platform · Organization · Common · HR Basics        │
│           (+ tenant engine, universal roles, extension reg.)  │
├─────────────────────────────────────────────────────────────┤
│ LAYER 0 — frappe  (the framework = Universal ERP Core)        │
│           auth · RBAC · workflow · portal · web form · REST · │
│           files · notifications · dashboards · reports · jobs  │
└─────────────────────────────────────────────────────────────┘
```

**Dependencies point downward only.** `required_apps = ["frappe"]`.

## Modules

| Module | Purpose | Key doctypes |
|---|---|---|
| **Platform** | Settings, workspace, extension registry | CoreERP Settings |
| **Organization** | Tenant / business-unit root + tenant isolation | Organization |
| **Common** | Shared masters | UOM, UOM Conversion Factor, Territory, Brand, Terms and Conditions |
| **HR Basics** | Org-structure & people (no payroll) | Department, Designation, Branch, Employee Profile, Holiday List, Holiday |

13 doctypes total. Universal roles: Organization Manager, Platform Admin, HR Basic User,
Portal Client.

## What we deliberately leave out

- **No CRM/sales/projects/support** (Client, Vendor, Lead, Opportunity, Project, Task,
  Ticket, SLA). These are domain-specific — build them in your own app, not the universal core.
- **No accounting / stock / manufacturing.** No Account, Item, Warehouse, BOM, Work Order.
- **No `doc_events["*"]`.** Every document event is scoped to a specific doctype.
- **No transactional portal routes.** No `/orders`, `/invoices`, `/boms`.

See `doctype-classification.md`.

## Cross-cutting concerns

- **Multi-tenancy** → `coreerp/organization/tenant.py` (row-level) or site-per-tenant. See `RBAC-guide.md`.
- **Extensibility** → `coreerp/platform/extensions.py` registry. See `plugin-development-guide.md`.
- **Boot context** → `coreerp/setup/boot.py` injects org context into `frappe.boot.coreerp`.
- **Public API** → `coreerp/api/platform.py` (`/api/method/coreerp.api.platform.*`).
