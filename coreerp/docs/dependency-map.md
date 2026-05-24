# CoreERP — Dependency Map

## App-level

```
coreerp ──required_apps──▶ frappe
coreerp ──(never)────────▶ erpnext     ✗ enforced by scripts/validate.py (AST import check)
```

## Doctype link graph (CoreERP internal + Frappe-core targets)

Frappe-core targets in **[brackets]**.

```
Organization ──parent_organization──▶ Organization (tree)
Organization ──▶ [Currency] [Country]

Client   ──client_group──▶ Client Group (tree)
Client   ──▶ Organization, Territory, Market Segment, [Currency] [Language] [Contact] [Address]
Vendor   ──vendor_group──▶ Vendor Group (tree)
Vendor   ──▶ Organization, [Currency] [Language] [Country] [Contact] [Address]

Lead        ──▶ Organization, Lead Source, Market Segment, Territory, [User] [Language]
Opportunity ──party(Dynamic Link)──▶ Lead | Client
Opportunity ──▶ Organization, Lead Source, Market Segment, [Currency] [User]
Opportunity ──items──▶ Opportunity Item ──uom──▶ UOM
Campaign    ──▶ Organization

Project   ──▶ Organization, Client, Project Type, [User]
Project   ──users──▶ Project User ──▶ [User]
Task      ──project──▶ Project ; ──parent_task──▶ Task ; ──▶ Task Type, [User], Organization
Timesheet ──▶ Organization, Project(parent_project), Employee Profile
Timesheet ──time_logs──▶ Timesheet Detail ──▶ Task, Project, Activity Type

Ticket ──▶ Organization, Client, Ticket Priority, Ticket Type, Service Level Agreement, [Contact] [User]
Service Level Agreement ──priorities──▶ SLA Priority ──priority──▶ Ticket Priority
Service Level Agreement ──▶ Organization

Department ──parent_department──▶ Department (tree) ; ──▶ Organization
Branch ──▶ Organization
Employee Profile ──▶ Organization, Department, Designation, Branch, Holiday List,
                     reports_to(Employee Profile), [User] [Gender]
Holiday List ──holidays──▶ Holiday ; ──▶ Organization
Territory ──parent_territory──▶ Territory (tree)
UOM Conversion Factor ──from_uom/to_uom──▶ UOM

CoreERP Settings (Single) ──▶ Organization, [Currency] [Role]
```

## Circular dependencies

**None.** Self-referential trees (Organization, Department, Territory, Client/Vendor Group, Task)
are intentional nested-set hierarchies, not cycles. The only cross-module two-way relation is
Opportunity↔(Lead|Client) via a one-directional Dynamic Link.

## Load order

Frappe resolves doctype creation order automatically from link dependencies during
`bench migrate`. Trees and child tables are created before their parents reference them.
No manual ordering is required. Masters (UOM, Territory, Organization) have no inbound
dependencies and load first; transactional doctypes (Project, Ticket, Opportunity) load last.

## Hook dependency surface

| Hook | Targets | File |
|---|---|---|
| `doc_events` | Ticket, Task, Timesheet, Project (scoped) | per-doctype controllers |
| `permission_query_conditions` / `has_permission` | 8 tenant-scoped doctypes | `organization/tenant.py` |
| `scheduler_events` | Ticket, Opportunity, Task, SLA | per-doctype controllers |
| `boot_session` | — | `setup/boot.py` |
| `after_install` / `after_migrate` | — | `setup/install.py` |
