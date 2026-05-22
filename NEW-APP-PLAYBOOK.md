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

My environment (frappe_docker devcontainer):
- I use the official frappe_docker devcontainer; the bench lives at
  /workspace/development/frappe-bench (Frappe v15). MariaDB host = `mariadb`,
  Redis = `redis-cache:6379` / `redis-queue:6379`, DB root password = 123.
- Where you (Claude Code) run bench: <"inside the devcontainer" OR "from host via
  docker exec <devcontainer>-frappe-1">. Use the matching `B()` helper from section 1.

What I want to build:
- New app name: <e.g. campusflow>  (snake_case, lowercase)
- Domain / purpose: <one sentence, e.g. "university ERP: admissions, courses, hostel">
- Site name: <e.g. campusflow.localhost>
- CoreERP source: bench get-app https://github.com/zopeeeeee/coreerp.git

RULES:
1. Use my frappe_docker devcontainer bench at /workspace/development/frappe-bench
   (section 1). Create a dedicated site for THIS project. Do NOT install into or modify
   any unrelated bench/site I already use for another project.
2. Install order: ensure bench exists (Frappe v15, section 2) -> get-app coreerp
   (section 3) -> new-site + install-app coreerp (section 4) -> new-app + install my app
   (section 5).
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

Start with section 1 (confirm the devcontainer bench + pick the right B() helper), then
proceed in order.
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

## 1. Bring up the frappe_docker devcontainer

This is the **official** Frappe dev setup: `frappe_docker` provides a VS Code devcontainer
that runs MariaDB + Redis + a dev container; you then create the bench *inside* it at
`/workspace/development`.

```bash
# on the host
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
cp -r devcontainer-example .devcontainer
cp -r development/vscode-example development/.vscode
# open in VS Code and "Reopen in Container" (or: docker compose -f .devcontainer/docker-compose.yml up -d)
code .
```

Inside the devcontainer, the working tree is `/workspace/development`. MariaDB is reachable
at host `mariadb`, Redis at `redis-cache:6379` / `redis-queue:6379` (already wired by the
devcontainer compose). The DB root password is `123` by default.

### How Claude Code runs bench (pick the one that matches where it's running)

**A) Claude Code is INSIDE the devcontainer** (VS Code "Reopen in Container" terminal):
run bench directly.
```bash
cd /workspace/development/frappe-bench && bench <args>
```

**B) Claude Code is on the WINDOWS HOST**, exec-ing into the devcontainer:
```bash
# find the container name once:  docker ps   (e.g. <devcontainer>-frappe-1)
docker exec <devcontainer>-frappe-1 bash -lc "cd /workspace/development/frappe-bench && bench <args>"
```

For the rest of this guide a single helper covers both — define whichever applies:
```bash
# inside container:
B() { cd /workspace/development/frappe-bench && bench "$@"; }
# OR on host:
# B() { docker exec <devcontainer>-frappe-1 bash -lc "cd /workspace/development/frappe-bench && bench $*"; }
```

> **Isolation rule for Claude Code:** create/use a bench dedicated to THIS project. Do NOT
> install your new app into an unrelated existing bench/site you already use for another
> project.

---

## 2. Create the bench inside the devcontainer (Frappe v15)

Run inside `/workspace/development`:
```bash
# (host form: docker exec <devcontainer>-frappe-1 bash -lc "cd /workspace/development && bench init ...")
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench
# the devcontainer already provides mariadb/redis hosts; if config is missing, set:
bench set-config -g db_host mariadb
bench set-config -g redis_cache  "redis://redis-cache:6379"
bench set-config -g redis_queue  "redis://redis-queue:6379"
bench set-config -g redis_socketio "redis://redis-queue:6379"
```

> The stock `frappe_docker` devcontainer already points new benches at `mariadb`/`redis-*`,
> so the `set-config` lines are usually a no-op safety net.

---

## 3. Get CoreERP into the bench

```bash
B get-app https://github.com/zopeeeeee/coreerp.git
```

That clones CoreERP into `apps/coreerp`, installs it into the bench env, and adds it to
`apps.txt` correctly. (You install it onto a *site* in section 4.)

> **Pitfall (only if you ever add an app to `apps.txt` by hand):** it needs one app per
> line WITH a trailing newline. `echo coreerp >> sites/apps.txt` after a file with no
> final newline yields `frappecoreerp`. Use `printf 'frappe\ncoreerp\n' > sites/apps.txt`.
> `bench get-app` does this for you — prefer it.

---

## 4. Create a site and install CoreERP

```bash
B new-site myproject.localhost --db-root-password 123 --admin-password admin --no-mariadb-socket
B --site myproject.localhost install-app coreerp
B --site myproject.localhost migrate
```

---

## 5. Scaffold YOUR new app

```bash
B new-app myproduct
# in apps/myproduct/myproduct/hooks.py set:   required_apps = ["frappe", "coreerp"]
B --site myproject.localhost install-app myproduct
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
B build --app coreerp --app myproduct
B use myproject.localhost          # set as default site for `bench start`
```

Start the dev server. In the **frappe_docker devcontainer** the normal way is `bench start`
(runs web + workers + socketio); VS Code forwards container port **8000** to the host.
```bash
# inside the devcontainer (a long-running terminal):
cd /workspace/development/frappe-bench && bench start
# host form (detached single web process if you don't use bench start):
# docker exec -d <devcontainer>-frappe-1 bash -lc \
#   "cd /workspace/development/frappe-bench && exec bench serve --port 8000 > /tmp/web.log 2>&1"
```

Open **http://myproject.localhost:8000** (the devcontainer forwards 8000). Login
`Administrator` / `admin`.
(Browsers auto-resolve `*.localhost`. If not, add `127.0.0.1 myproject.localhost` to
`C:\Windows\System32\drivers\etc\hosts`. If VS Code forwarded 8000 to a different host
port, use that port.)

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
B --site myproject.localhost execute coreerp.setup.install.mark_setup_complete
B --site myproject.localhost clear-cache
# then restart bench start (Ctrl+C and re-run it), or restart the serve process
```
Then **hard-refresh** (Ctrl+Shift+R) or use Incognito — a normal refresh keeps the stale
cached `frappe.boot`.

---

## 10. Verify your app (don't trust static checks alone)

Write a `myproduct/tests/smoke.py` with a `run()` that creates one of each key doctype and
exercises your doc_events, then:
```bash
# inside the devcontainer:
cd /workspace/development/frappe-bench/sites && \
  ../env/bin/python -c "import frappe; frappe.init(site='myproject.localhost'); frappe.connect(); import myproduct.tests.smoke as s; s.run()"
# host form: docker exec <devcontainer>-frappe-1 bash -lc "cd /workspace/development/frappe-bench/sites && ../env/bin/python -c \"...\""
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
B --site myproject.localhost migrate        # apply schema/patches
B --site myproject.localhost clear-cache    # after config/boot changes
B build --app myproduct                     # rebuild JS/CSS
B --site myproject.localhost console        # interactive shell
B start                                      # run web + workers + socketio (devcontainer)
# devcontainer lifecycle (host): VS Code "Reopen in Container" / "Close Remote Connection",
# or `docker compose -f .devcontainer/docker-compose.yml down` from the frappe_docker dir.
```

That's the whole loop: **devcontainer → bench → coreerp → your app → reuse → verify → ship.**
