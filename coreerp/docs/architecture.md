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
│ LAYER 1 — coreerp  (THIS APP)                                 │
│           Organization · Parties · Common · HR Basics ·       │
│           Engagement · Projects · Service                     │
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
| **Platform** | Platform settings, workspace, extension registry | CoreERP Settings |
| **Organization** | Tenant / business-unit root + tenant isolation | Organization |
| **Parties** | Neutral party masters | Client, Vendor, Client Group, Vendor Group, Party Type |
| **Common** | Shared masters | UOM, UOM Conversion Factor, Territory, Brand, Terms and Conditions |
| **HR Basics** | Org-structure & people (no payroll) | Department, Designation, Branch, Employee Profile, Holiday List, Holiday |
| **Engagement** | Lightweight CRM | Lead, Opportunity (+Item), Campaign, Lead Source, Market Segment |
| **Projects** | Delivery tracking (no billing) | Project, Task, Timesheet (+Detail), Project/Task/Activity Type, Project User |
| **Service** | Helpdesk / SLA | Ticket, Service Level Agreement (+SLA Priority), Ticket Priority, Ticket Type |

37 doctypes total.

## What we deliberately removed vs ERPNext

- **No accounting coupling.** Client/Vendor have no `PartyAccount` child table and make no
  `validate_party_accounts` call. Organization has no default-account fields.
- **No stock/manufacturing.** No Item, Warehouse, BOM, Work Order, Stock Entry.
- **No billing in Projects.** Project/Timesheet drop `gross_margin`, `sales_invoice`, costing.
- **No `doc_events["*"]`.** Every document event is scoped to a specific doctype.
- **No transactional portal routes.** No `/orders`, `/invoices`, `/boms`.

See `doctype-classification.md` and the repo-root `MANUFACTURING-REMOVAL-REPORT.md`.

## Cross-cutting concerns

- **Multi-tenancy** → `coreerp/organization/tenant.py` (row-level) or site-per-tenant. See `RBAC-guide.md`.
- **Extensibility** → `coreerp/platform/extensions.py` registry. See `plugin-development-guide.md`.
- **Boot context** → `coreerp/setup/boot.py` injects org context into `frappe.boot.coreerp`.
- **Public API** → `coreerp/api/platform.py` (`/api/method/coreerp.api.platform.*`).
