# CoreERP — Setup & Bench Installation

## Prerequisites
A working [Frappe Bench](https://github.com/frappe/bench) (Frappe v15+), MariaDB/Postgres, Redis,
Node. (CoreERP itself adds no extra Python deps — it's a pure platform layer.)

## Install

```bash
# 1. Add the app to your bench
bench get-app coreerp /path/to/coreerp          # local path
#   or: bench get-app https://github.com/your-org/coreerp.git

# 2. Create a site (or reuse one)
bench new-site mysite.localhost

# 3. Install CoreERP onto the site
bench --site mysite.localhost install-app coreerp

# 4. Start / open
bench start                                       # if not already running
bench --site mysite.localhost browse --user Administrator
```

## What a fresh install gives you (baseline mode)
- The **CoreERP** workspace as a clean landing page (Parties / Engagement / Projects / Service /
  HR Basics / Setup cards).
- Default roles + role profiles (CoreERP Admin/CRM/Projects/Service).
- A default **Organization** ("My Organization").
- Party Types (Client, Vendor), Portal default role (Portal Client).
- **No** accounting, stock, manufacturing, or heavy ERP menus.

## Optional: setup wizard
The minimal CoreERP wizard captures the first Organization + currency. Run it via
Desk → setup, or skip it (defaults are created on install).

## Enable row-level multi-tenancy (optional)
1. CoreERP Settings → **Enable Row-Level Tenant Isolation** ✅.
2. For each user, add a User Permission: `allow = Organization`, `for_value = <org>`.
   (Or use site-per-tenant for hard isolation — see `coreerp/docs/RBAC-guide.md`.)

## Build a product on top
```bash
bench new-app myproduct          # set required_apps = ["frappe", "coreerp"]
bench --site mysite.localhost install-app myproduct
```
See `coreerp/docs/plugin-development-guide.md`.

## Uninstall
```bash
bench --site mysite.localhost uninstall-app coreerp
```

## Developer notes
- `_scaffold.py` and `_validate.py` at the repo root are **build tools**, not shipped at runtime
  (excluded by the `_`-prefix and not imported anywhere). Run `python _validate.py` after editing
  doctypes to catch dangling links / erpnext imports / global doc_events before `bench migrate`.
