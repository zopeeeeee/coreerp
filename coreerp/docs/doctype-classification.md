# CoreERP — Doctype Classification (slim universal core)

The **13** CoreERP doctypes. CoreERP ships only what is *universal* to any business app —
no CRM/sales/projects/support (those are domain-specific; add them per-app).

Origin codes:
- **NEW** — authored fresh for CoreERP (MIT), no copied code.
- **NEW (was X)** — clean re-model of an ERPNext concept X, rebuilt neutral (not ported).

| Module | Doctype | Type | Origin | Tenant-scoped |
|---|---|---|---|---|
| Platform | CoreERP Settings | Single | NEW | — |
| Organization | Organization | Tree | NEW (was Company; no account fields) | root |
| Common | UOM | Master | NEW | — |
| Common | UOM Conversion Factor | Master | NEW | — |
| Common | Territory | Tree | NEW | — |
| Common | Brand | Master | NEW | — |
| Common | Terms and Conditions | Master | NEW | — |
| HR Basics | Department | Tree | NEW | — |
| HR Basics | Designation | Master | NEW | — |
| HR Basics | Branch | Master | NEW | — |
| HR Basics | Employee Profile | Master | NEW (was Employee, HR-basics only) | ✅ |
| HR Basics | Holiday List | Master | NEW | ✅ |
| HR Basics | Holiday | Child | NEW | — |

## Universal roles (4)
Organization Manager · Platform Admin · HR Basic User · Portal Client.
Role profiles: CoreERP Admin, CoreERP HR.

## Deliberately NOT in the universal core
Removed as domain-specific (build them in your own app when needed):
- **CRM/sales:** Client, Vendor, Client/Vendor Group, Party Type, Lead, Opportunity,
  Campaign, Lead Source, Market Segment
- **Projects:** Project, Task, Timesheet, Project/Task/Activity Type
- **Support:** Ticket, Service Level Agreement, Ticket Priority/Type

Also excluded (Frappe/ERPNext domain): accounting, stock, manufacturing, assets, buying/
selling transactions, regional/telephony/quality verticals.

## What you reuse on top of Frappe
Organization (tenant root) · row-level **tenant-isolation engine**
(`coreerp.organization.tenant`) · universal masters · HR basics · universal roles ·
the **extension registry** (`coreerp.platform.extensions`) so downstream apps register
their own tenant doctypes / dashboards / portal items without forking CoreERP.
