# CoreERP — Build Report

What was built, how, and the provenance of every part. This is the answer to the
"FINAL OUTPUTS REQUIRED" section of the brief.

---

## 1. What this is

A real, installable Frappe app — **CoreERP** — providing an industry-agnostic ERP Foundation.
Built **clean from scratch** (MIT licensed), not copied from ERPNext. `required_apps = ["frappe"]`;
zero `erpnext` imports (enforced by `_validate.py`).

- 8 modules · **37 doctypes** · scoped hooks · plugin registry · install/setup/patches · workspace ·
  10 developer docs.
- Static validation: **37 doctypes discovered, 0 errors, 0 warnings.**
- **Live-verified** on Frappe v15: `install-app` + `migrate` clean, smoke test **13/13**
  (see §Verification and VALIDATION-CHECKLIST.md).

> Module note: the platform/settings module is named **`Platform`** (folder `coreerp/platform/`).
> An earlier draft used `CoreERP`/`Core`, which collided with Frappe's built-in `Core` module —
> caught and fixed during live verification.

---

## 0. Verification (live, Frappe v15)

Installed into an **isolated** Docker stack (own MariaDB 11.8 + Redis + `frappe/bench`, separate
network — the user's existing project containers were left untouched). Site `coreerp.localhost`,
Frappe 15.105.0.

`bench install-app coreerp` → `CoreERP: baseline platform installed.` · `bench migrate` clean and
idempotent (run twice). Runtime smoke test `coreerp/tests/smoke.py` → **13/13 PASS** covering CRUD,
all 4 doc_events, fetch_from, Lead→Client conversion, all 4 scheduler jobs, role permissions,
real tenant isolation (User Permission), and the REST API (token-authed whoami/summary/modules).
HTTP probes: ping/login/home 200, guest API 403.

### Bugs found by verification and fixed (this is why running it mattered)
| # | Bug | Fix |
|---|---|---|
| 1 | Module `CoreERP` (modules.txt) had no matching folder → `ModuleNotFoundError: coreerp.coreerp` | placed module content under a real folder |
| 2 | Renamed to `Core` → collided with Frappe's built-in **Core** module (broke `Module Def` load) | renamed module to **`Platform`** (folder `coreerp/platform/`) |
| 3 | Employee Profile had a **duplicate `autoname`** key (`format:` + leftover `naming_series:`) → `AttributeError: naming_series` | removed the stray key |
| 4 | `has_permission` hook wrong signature — crashed on the `doc=None` doctype-level call → `PermissionError` on every list | signature `has_permission(doc=None, ptype=None, user=None)`, allow when `doc is None` |
| 5 | `permission_query_conditions` returned a bare-column clause with `OR organization IS NULL` → tenant isolation leaked | table-qualified `` `tab<DocType>`.`organization` IN (...) ``, dropped the `OR NULL` |

All five fixes are in the host repo and re-pass static validation (0 errors).

---

## 2. File move/copy map

**There was no file copying.** Per the architecture decision (see `PLATFORM-ANALYSIS/` and the
README), the reusable "core" doctypes you listed (User, Role, Workflow, File, Communication, Web
Page, Web Form, OAuth, ToDo, Version, Error Log, Comment, DocShare, Email Queue, Scheduled Job
Type, …) are **Frappe framework doctypes** — a Frappe app cannot and must not redefine them. They
are *inherited* by depending on `frappe`, not moved.

What was authored fresh in CoreERP (the generic business layer that is NOT in Frappe):

| CoreERP doctype | Conceptual origin (ERPNext) | Relationship |
|---|---|---|
| Organization | Company | clean re-model (no account fields) |
| Client | Customer | clean re-model (no PartyAccount) |
| Vendor | Supplier | clean re-model (no PartyAccount) |
| Client/Vendor Group | Customer/Supplier Group | clean re-model (no `accounts`) |
| Employee Profile | Employee | HR-basics subset |
| Project / Task / Timesheet | same | de-financed |
| Lead / Opportunity (+Item) | same | de-coupled from selling/tax |
| Ticket / SLA / priorities | Issue / Service Level Agreement | de-coupled |
| UOM / Territory / Brand / Terms / Party Type / Campaign / etc. | same names | fresh authoring |

So the "move map" is really a **re-model map**: ERPNext concept → fresh neutral CoreERP doctype.
Full table in `coreerp/docs/doctype-classification.md`.

---

## 3. Dependency cleanup report

| Coupling in ERPNext | How CoreERP avoids it |
|---|---|
| `customer.py` → `erpnext.accounts.party.validate_party_accounts` | Client has no accounts; no such import |
| `supplier.py` → `erpnext.accounts.party` + PartyAccount table | Vendor is pure data |
| `company.py` → 14 default-account fields | Organization has none (finance plugin adds via Custom Field) |
| `lead.py` → `SellingController`, `accounts.party.set_taxes` | Lead subclasses `Document` |
| `opportunity.py` → `TransactionBase`, `get_exchange_rate` | Opportunity subclasses `Document` |
| `project.py`/`timesheet.py` costing/billing + Sales Invoice link | removed; pure delivery/time |
| `doc_events["*"]` global validate (SLA + deletion) | scoped doc_events only; build fails on `"*"` |
| accounting-dimension field injection (~60 doctypes) | not present |
| manufacturing/stock/asset scheduler jobs | not present; only neutral jobs |
| transactional portal routes (`/orders`, `/boms`, …) | only `/projects`, `/tickets` |
| `extend_doctype_class` Address→ERPNextAddress (GST) | not present |
| regional monkey-patches (`regional_overrides`) | not present |

**Validation evidence:** `python _validate.py` → AST-level import scan finds **0** `erpnext` imports
across all 37 controllers + infra modules.

---

## 4. Manufacturing removal report

CoreERP **never contained** manufacturing — it was built clean — so "removal" = "excluded by
construction." The following ERPNext areas are absent and intended to be **plugins/product apps**:

- Manufacturing (47): BOM, Work Order, Job Card, Routing, Operation, Workstation, Production Plan,
  Master Production Schedule, Blanket Order, Plant Floor, Manufacturing Settings, Sales Forecast.
- Stock (77): Item, Warehouse, Stock Entry, Stock Ledger Entry, Batch, Serial No, Delivery Note,
  Purchase Receipt, Bin, Pick List, Material Request, Repost Item Valuation.
- Accounts (191), Assets (26), Subcontracting (13), Buying/Selling transactions (37).

There are **no orphaned hooks, scheduler entries, patches, fields, or workspace links** referencing
these — confirmed because none were ever added. Contrast with Strategy B in
`PLATFORM-ANALYSIS/04-manufacturing-removal-plan.md`, which shows why removing them *from* ERPNext
is fragile (shared controller spine). CoreERP sidesteps that entirely.

---

## 5. Module boundaries (suggested + implemented)

```
CoreERP       platform settings, workspace, extension registry
Organization  tenant root + isolation        ← foundation, no deps on other modules
Common        shared masters (UOM, Territory, Brand, Terms)  ← no deps
Parties       Client/Vendor (+ groups)        ← deps: Organization, Common
HR Basics     people & org structure          ← deps: Organization
Engagement    CRM (Lead/Opportunity/Campaign) ← deps: Organization, Parties, Common
Projects      delivery (Project/Task/Timesheet)← deps: Organization, Parties, HR
Service       helpdesk (Ticket/SLA)           ← deps: Organization, Parties
```
Clean DAG, no cycles (see `coreerp/docs/dependency-map.md`).

---

## 6. Recommended repo structure
See `coreerp/docs/architecture.md`. Mirrors professional Frappe apps (frappe/erpnext layout):
`pyproject.toml`, `license.txt`, `MANIFEST.in`, `coreerp/{hooks.py, modules.txt, patches.txt,
<module>/doctype/..., setup/, api/, core/, patches/, docs/}`.

---

## 7. Technical debt list
See `TECH-DEBT.md`.

## 8. Refactoring opportunities
See `TECH-DEBT.md` (same file, second section).

## 9. Future plugin architecture recommendations
See `coreerp/docs/plugin-development-guide.md` and `PLATFORM-ANALYSIS/08-plugin-architecture.md`.

## 10. Setup & bench installation
See `SETUP.md`.

## 11. Validation
See `VALIDATION-CHECKLIST.md`.
