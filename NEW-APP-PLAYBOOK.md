# CoreERP — New Application Playbook

The end-to-end guide for spinning up a fresh environment and building a new business
app on **CoreERP** (no ERPNext). Follow it top to bottom every time you start a new
product. Tested on Frappe **v15**, Docker, Windows host.

---

## 📋 COPY-PASTE THIS PROMPT TO CLAUDE CODE

> Paste the block below into Claude Code. Fill in the `<...>` placeholders first.

```text
You are setting up a brand-new Frappe application built on CoreERP (NOT ERPNext).
Follow the guide in NEW-APP-PLAYBOOK.md EXACTLY, phase by phase (sections 1 through 12),
in order. Do not improvise an alternative stack or skip the verification.

What I want to build:
- New app name: <e.g. campusflow>  (snake_case, lowercase)
- Domain / purpose: <one sentence, e.g. "university ERP: admissions, courses, hostel">
- Site name: <e.g. campusflow.localhost>
- Host port for the web UI: <e.g. 8460 — must be free on my machine>
- CoreERP source: bench get-app https://github.com/zopeeeeee/coreerp.git

RULES:
1. Use the ISOLATED Docker stack from section 1 (own MariaDB + Redis + bench, unique
   container names + network derived from the app name). Do NOT reuse or touch any of
   my existing Docker containers.
2. Install order: init bench (Frappe v15, section 2) -> get-app coreerp (section 3) ->
   new-site + install-app coreerp (section 4) -> new-app + install my app (section 5).
3. Obey the skeleton conventions in section 5 EXACTLY:
   - module names in modules.txt unique AND mapped to a real folder; never reuse a
     Frappe-builtin module name (Core, Website, Desk, ...).
   - every doctype has .json + .py (a Document subclass) + __init__.py, INCLUDING child
     tables.
   - exactly one autoname per doctype.
4. REUSE the platform (section 6): link to CoreERP Organization/Client/Vendor; reuse its
   roles; wire tenant isolation via coreerp_extensions + permission_query_conditions ->
   coreerp.organization.tenant; extend platform masters with Custom Field fixtures, never
   by editing CoreERP.
5. Obey section 7: NEVER register doc_events["*"]; no finance/stock scheduler jobs;
   composition over inheritance.
6. After install, build assets and start the dev server (section 8) and confirm the site
   is reachable; the setup wizard is mine to fill (don't auto-complete it unless I ask).
7. Be aware of the two known Frappe quirks in section 9 (legacy roles are harmless;
   CoreERP heals the setup-wizard loop) — don't "fix" the legacy roles.
8. WRITE AND RUN a smoke test (section 10) that creates one of each key doctype and
   exercises my doc_events, and show me it passes. Do not claim it works without running it.
9. Use a todo list, give a short status after each section, and tell me the browser URL +
   login when done. Then do section 11 (git init + gh repo create --private) only if I
   confirm.

Start with section 1 (bring up the isolated stack), then proceed in order.
```

---

## 0. Mental model (read once)

```
your_new_app   (depends on coreerp + frappe)   ← you build this
   └─ coreerp   (platform: Organization, Client, Vendor, roles, tenant, registry)
        └─ frappe (framework: auth, RBAC, workflow, portal, REST, jobs)
```

Rule: **dependencies point down only.** Your app links to CoreERP doctypes and reuses
its roles/tenant/registry. CoreERP never depends on your app. Finance/stock/manufacturing
are *optional plugins*, never assumed.

---

## 1. Bring up an isolated Frappe stack (Docker)

You don't need to install MariaDB/Redis/bench on Windows — run them in containers.
Use a dedicated stack per project so nothing collides.

Create `myproject-stack/docker-compose.yml`:

```yaml
name: myproject
services:
  mariadb:
    image: mariadb:11.8
    container_name: myproject-mariadb
    command: [--character-set-server=utf8mb4, --collation-server=utf8mb4_unicode_ci, --skip-character-set-client-handshake]
    environment: { MARIADB_ROOT_PASSWORD: "123" }
    volumes: [mariadb-data:/var/lib/mysql]
    networks: [myproject_net]
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 5s
      timeout: 5s
      retries: 20
  redis-cache:  { image: redis:7-alpine, container_name: myproject-redis-cache, networks: [myproject_net] }
  redis-queue:  { image: redis:7-alpine, container_name: myproject-redis-queue, networks: [myproject_net] }
  bench:
    image: frappe/bench:latest
    container_name: myproject-bench
    command: sleep infinity
    working_dir: /home/frappe
    user: frappe
    volumes: [bench-data:/home/frappe]
    ports: ["8456:8000", "9456:9000"]   # pick host ports that are free
    networks: [myproject_net]
    depends_on: { mariadb: { condition: service_healthy } }
networks: { myproject_net: { name: myproject_net } }
volumes: { mariadb-data: {}, bench-data: {} }
```

```bash
cd myproject-stack && docker compose up -d
```

> Pick **free host ports** for `8456`/`9456`. If `docker compose up` says
> "port is already allocated", change them.

Helper alias for the rest of this guide:
```bash
D() { docker exec myproject-bench bash -lc "cd /home/frappe/frappe-bench && $*"; }
```

---

## 2. Initialize the bench (Frappe v15)

```bash
docker exec myproject-bench bash -lc \
  "cd /home/frappe && bench init --frappe-branch version-15 --skip-redis-config-generation frappe-bench"

# point bench at the containerized services
D "bench set-config -g db_host mariadb"
D "bench set-config -g redis_cache 'redis://redis-cache:6379'"
D "bench set-config -g redis_queue 'redis://redis-queue:6379'"
D "bench set-config -g redis_socketio 'redis://redis-queue:6379'"
```

---

## 3. Get CoreERP into the bench

```bash
# from a git remote (recommended once pushed):
D "bench get-app https://github.com/zopeeeeee/coreerp.git"

# OR from a local path (mount or docker cp the folder in first):
#   docker cp /path/to/coreerp myproject-bench:/home/frappe/frappe-bench/apps/coreerp
#   D "./env/bin/pip install -e apps/coreerp"
#   D "printf 'frappe\ncoreerp\n' > sites/apps.txt"   # ensure trailing newline!
```

> **Pitfall:** `apps.txt` needs one app per line WITH a trailing newline. A common bug is
> `echo coreerp >> apps.txt` after a file with no final newline → `frappecoreerp`.
> Use `printf 'frappe\ncoreerp\n' > sites/apps.txt`.

---

## 4. Create a site and install CoreERP

```bash
D "bench new-site myproject.localhost --db-root-password 123 --admin-password admin --no-mariadb-socket"
D "bench --site myproject.localhost install-app coreerp"
D "bench --site myproject.localhost migrate"
```

---

## 5. Scaffold YOUR new app

```bash
D "bench new-app myproduct"
# in apps/myproduct/myproduct/hooks.py set:   required_apps = ["frappe", "coreerp"]
D "bench --site myproject.localhost install-app myproduct"
```

### App skeleton conventions (learned the hard way)
- **Module names in `modules.txt` must be globally unique AND map to a real folder.**
  Module `Foo Bar` → folder `foo_bar/`. **Never** reuse a Frappe-builtin module name
  (`Core`, `Website`, `Desk`, …) — it collides and breaks `Module Def` loading.
  If your "main" module would map to the app's own root folder name, rename it
  (e.g. module `MyProduct Core` → folder `myproduct_core/`).
- **Every doctype needs all three files**: `<name>.json`, `<name>.py` (a `Document`
  subclass), and `__init__.py`. A missing `.py` — even for a **child table** — causes
  `ModuleNotFoundError` on install.
- **One `autoname` only.** Don't set both `autoname` in JSON twice or mix `naming_series:`
  with `format:` — duplicate keys silently pick the wrong one (`AttributeError: naming_series`).

---

## 6. Reuse the CoreERP platform (the whole point)

### Link to platform masters
```json
{"fieldname": "client", "fieldtype": "Link", "options": "Client"}
{"fieldname": "organization", "fieldtype": "Link", "options": "Organization"}
```

### Reuse roles
Don't reinvent base roles. In your `setup/install.py after_install`, create only
domain-specific roles; reuse `Organization Manager`, `Portal Client`, etc. where they fit.

### Reuse tenant isolation (multi-tenant for free)
Add an `organization` Link field to each tenant-scoped doctype, then in your `hooks.py`:
```python
coreerp_extensions = {"tenant_doctypes": ["My Doctype", "Another"]}
permission_query_conditions = {
    "My Doctype": "coreerp.organization.tenant.get_permission_query_conditions",
}
has_permission = {
    "My Doctype": "coreerp.organization.tenant.has_permission",
}
```
Then give each user a User Permission (`allow=Organization, for_value=<org>,
apply_to_all_doctypes=1`) and they only see their org's data — across the desk, reports,
and REST, with no extra code.

> **Tenant rule:** a tenant-scoped doctype MUST have an `organization` column. Records with
> a NULL organization are HIDDEN from restricted users (isolation stays honest).

### Reuse the extension registry
Contribute to CoreERP extension points from your `hooks.py`:
```python
coreerp_extensions = {
    "party_dashboards":   ["myproduct.api.extend.something"],
    "workspace_shortcuts": ["myproduct.api.extend.shortcuts"],
    "tenant_doctypes":    ["My Doctype"],
}
```

### Extend platform masters WITHOUT editing CoreERP
Need an extra field on `Client` or `Organization`? Ship a **Custom Field fixture** in your
app — never modify CoreERP's JSON:
```python
# myproduct/hooks.py
fixtures = [{"dt": "Custom Field", "filters": [["dt", "in", ["Client", "Organization"]]]}]
```

---

## 7. Cross-cutting rules (avoid the ERPNext mistakes)

- **NEVER register `doc_events["*"]`.** Scope every event to a named doctype. The global
  validate hook is the #1 source of coupling in ERPNext.
- **No domain-finance scheduler jobs** in a generic app.
- **Composition over inheritance** — opt into behavior per doctype; don't build a god
  controller everything must subclass.

---

## 8. Build assets, run the server, view in browser

```bash
D "bench build --app coreerp --app myproduct"
# start the dev web server (detached so it survives the shell)
docker exec -d myproject-bench bash -lc \
  "cd /home/frappe/frappe-bench && exec bench --site myproject.localhost serve --port 8000 > /tmp/web.log 2>&1"
```

Open **http://myproject.localhost:8456** — login `Administrator` / `admin`.
(Browsers auto-resolve `*.localhost`. If not, add `127.0.0.1 myproject.localhost` to
`C:\Windows\System32\drivers\etc\hosts`.)

First load shows the **setup wizard** — fill it once; you then land on the desk.

---

## 9. Two known Frappe quirks (not bugs in your app)

### a) The "ERPNext-looking" roles
A fresh Frappe site (no ERPNext) still shows roles like **Sales User, Accounts Manager,
Purchase User, Maintenance Manager**. These come from **Frappe itself** — its `Contact`,
`Address`, and `Currency` doctypes ship permission rows referencing those roles (legacy of
Frappe + ERPNext co-development), so installing the `frappe` app auto-creates them. They are
NOT from CoreERP or your app, and they're harmless. To hide them: open each Role and tick
**Disabled** (don't delete — Contact/Address reference them).

### b) The setup-wizard loop (already fixed in CoreERP)
On a no-ERPNext site, the desk could loop on `/app/setup-wizard` because Frappe's
`is_setup_complete()` only inspects `frappe`/`erpnext` and the install sets the desk home
page to `setup-wizard`. CoreERP heals this in `after_migrate`
(`coreerp.setup.install.heal_setup_wizard_loop`). If you ever hit it:
```bash
D "bench --site myproject.localhost execute coreerp.setup.install.mark_setup_complete"
D "bench --site myproject.localhost clear-cache"
docker exec myproject-bench bash -lc "pkill -f 'bench.*serve'"
docker exec -d myproject-bench bash -lc "cd /home/frappe/frappe-bench && exec bench --site myproject.localhost serve --port 8000 > /tmp/web.log 2>&1"
```
Then **hard-refresh** (Ctrl+Shift+R) or use Incognito — a normal refresh keeps the stale
cached `frappe.boot`.

---

## 10. Verify your app (don't trust static checks alone)

Write a `myproduct/tests/smoke.py` with a `run()` that creates one of each key doctype and
exercises your doc_events, then:
```bash
D "cd sites && ../env/bin/python -c \"import frappe; frappe.init(site='myproject.localhost'); frappe.connect(); import myproduct.tests.smoke as s; s.run()\""
```
(`bench execute` can't import your app's modules directly — use this `frappe.init` form.)

CoreERP itself ships `coreerp/tests/smoke.py` (13 checks) as a reference pattern.

---

## 11. Git + GitHub

```bash
cd /path/to/myproduct
git init && git add -A && git commit -m "feat: myproduct v0.1 on CoreERP"
gh repo create zopeeeeee/myproduct --private --source=. --remote=origin --push
```

---

## 12. Lifecycle commands cheat-sheet

```bash
D "bench --site myproject.localhost migrate"        # apply schema/patches
D "bench --site myproject.localhost clear-cache"    # after config/boot changes
D "bench build --app myproduct"                     # rebuild JS/CSS
D "bench --site myproject.localhost console"        # interactive shell
docker compose down        # stop stack (keep data)
docker compose down -v     # stop + WIPE all data (full reset)
```

That's the whole loop: **stack → bench → coreerp → your app → reuse → verify → ship.**
