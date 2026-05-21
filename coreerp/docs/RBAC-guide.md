# CoreERP — RBAC & Multi-Tenancy Guide

CoreERP reuses Frappe's full permission stack and adds a thin, centralized tenant layer.
Source: `coreerp/organization/tenant.py`, role setup in `coreerp/setup/install.py`.

## Frappe permission layers (all available, unchanged)
1. **Role permissions** (DocPerm in each doctype JSON).
2. **if_owner** refinement (e.g. Portal Client sees only their own Tickets).
3. **User Permissions** (instance-level row filtering) — the tenant lever.
4. **Controller `has_permission`** hooks.
5. **DocShare** (ad-hoc sharing) + **Document Share Key** (tokenized links).
6. **permission_query_conditions** (SQL WHERE injection — list/report/REST share one rule).

See `PLATFORM-ANALYSIS/05-rbac-security-architecture.md` for the deep audit.

## CoreERP roles (shipped)
| Role | Desk | Purpose |
|---|---|---|
| Platform Admin | ✅ | Read-all oversight |
| Organization Manager | ✅ | Manage orgs, parties, vendors |
| CRM Manager / CRM User | ✅ | Engagement |
| Project Manager / Project Member | ✅ | Delivery |
| Service Manager / Service Agent | ✅ | Helpdesk |
| HR Basic User | ✅ | People/org structure |
| Portal Client | ❌ | External portal access (own records only) |

Role Profiles: **CoreERP Admin / CRM / Projects / Service** bundle these for quick assignment.

## Multi-tenancy

### Model A — site-per-tenant (hard isolation)
Each tenant = a separate Frappe **site** (separate DB). Nothing to configure in CoreERP; install
the app per site. Best for B2B SaaS / strong isolation.

### Model B — row-level (one site, many tenants)
1. Enable in **CoreERP Settings → Enable Row-Level Tenant Isolation**.
2. Each tenant-scoped doctype carries an `organization` Link field.
3. Give each user a **User Permission**: `allow=Organization`, `for_value=<their org>`.
4. CoreERP's `get_permission_query_conditions` filters all 8 scoped doctypes (and any registered
   via `coreerp_extensions["tenant_doctypes"]`) to the user's organization(s).

Bypass roles (never tenant-filtered): `Administrator`, `System Manager`, `Platform Admin`.

### How the filter works
```python
# coreerp/organization/tenant.py
get_allowed_organizations(user)  # from User Permission; [] = unrestricted
get_permission_query_conditions(user)  # -> "`organization` in (...) or `organization` is null"
has_permission(doc, user)              # single-doc mirror
has_website_permission(doc, ...)       # portal: own-org or own-record
```

## Portal users
Create them as **Website User** + assign **Portal Client**. They access `/projects` and `/tickets`
(portal menu), seeing only their own records via `if_owner` DocPerms + tenant `has_website_permission`.

## API auth
Frappe-native: API key/secret (`Authorization: token key:secret`), OAuth2/OIDC (OAuth Client +
Bearer Token, role-gated), social login. CoreERP adds no new auth — it inherits all of it.

## Recommended pattern
- Roles by job function; tenants by **one** Organization User Permission with `apply_to_all_doctypes`.
- Field-level secrets via `permlevel`. External access via DocShare, never extra roles.
- Always rely on `permission_query_conditions` so UI/report/REST enforce identically.
