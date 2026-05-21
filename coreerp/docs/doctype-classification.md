# CoreERP — Doctype Classification

The 37 CoreERP doctypes and their provenance relative to the Frappe+ERPNext analysis
(`PLATFORM-ANALYSIS/`). "Origin" = how this doctype came to be.

Origin codes:
- **NEW** — authored fresh for CoreERP (MIT), no copied code.
- **NEW(was X)** — clean re-model of a coupled ERPNext doctype X (rebuilt, not ported).
- **DECOUPLED(X)** — same concept as ERPNext X but stripped of finance/stock and re-parented.

| Module | Doctype | Type | Origin | Tenant-scoped |
|---|---|---|---|---|
| Platform | CoreERP Settings | Single | NEW | — |
| Organization | Organization | Tree | NEW (was Company) | root |
| Parties | Client | Master | NEW (was Customer) | ✅ |
| Parties | Vendor | Master | NEW (was Supplier) | ✅ |
| Parties | Client Group | Tree | NEW (was Customer Group) | — |
| Parties | Vendor Group | Tree | NEW (was Supplier Group) | — |
| Parties | Party Type | Master | NEW | — |
| Common | UOM | Master | NEW | — |
| Common | UOM Conversion Factor | Master | NEW | — |
| Common | Territory | Tree | NEW | — |
| Common | Brand | Master | NEW | — |
| Common | Terms and Conditions | Master | NEW | — |
| HR Basics | Department | Tree | NEW | — |
| HR Basics | Designation | Master | NEW | — |
| HR Basics | Branch | Master | NEW | — |
| HR Basics | Employee Profile | Master | NEW (was Employee, HR-basics only) | — |
| HR Basics | Holiday List | Master | NEW | — |
| HR Basics | Holiday | Child | NEW | — |
| Engagement | Lead | Transaction | DECOUPLED(Lead) | ✅ |
| Engagement | Opportunity | Transaction | DECOUPLED(Opportunity) | ✅ |
| Engagement | Opportunity Item | Child | DECOUPLED (generic, no stock Item) | — |
| Engagement | Campaign | Master | NEW | — |
| Engagement | Lead Source | Master | NEW | — |
| Engagement | Market Segment | Master | NEW | — |
| Projects | Project | Transaction | DECOUPLED(Project, no costing/billing) | ✅ |
| Projects | Task | Transaction | DECOUPLED(Task) | ✅ |
| Projects | Timesheet | Submittable | DECOUPLED(Timesheet, no sales_invoice) | ✅ |
| Projects | Timesheet Detail | Child | DECOUPLED | — |
| Projects | Project Type | Master | NEW | — |
| Projects | Task Type | Master | NEW | — |
| Projects | Activity Type | Master | NEW | — |
| Projects | Project User | Child | NEW | — |
| Service | Ticket | Transaction | DECOUPLED(Issue) | ✅ |
| Service | Service Level Agreement | Master | DECOUPLED(SLA) | — |
| Service | SLA Priority | Child | NEW | — |
| Service | Ticket Priority | Master | NEW (was Issue Priority) | — |
| Service | Ticket Type | Master | NEW (was Issue Type) | — |

## Excluded by design (never in CoreERP)
Accounting (Account, GL Entry, Journal Entry, Invoices, Tax, Fiscal Year), Stock (Item, Warehouse,
Stock Entry, Batch, Serial No), Manufacturing (BOM, Work Order, Routing, Job Card, Workstation,
Production Plan), Assets, Subcontracting, Buying/Selling transactions, regional/telephony/quality/
maintenance verticals. These belong in optional plugins or product apps.
