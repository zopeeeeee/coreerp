# CoreERP — How to Run & View in the Browser

This is the isolated Docker setup used to verify CoreERP (and the MediCare demo app) on
Frappe v15, completely separate from any other project containers.

## Open in the browser

- **URL:** http://coreerp.localhost:8456
- **Login:** `Administrator` / `admin`

After login (and completing the one-time setup wizard) you'll see two workspaces in the
left sidebar:
- **CoreERP** — the platform (Parties, Engagement, Projects, Service, HR Basics, Setup)
- **MediCare** — the hospital demo app built on top of CoreERP

> Browsers auto-resolve `*.localhost` to 127.0.0.1, so no hosts-file edit is needed. If
> yours doesn't, add `127.0.0.1 coreerp.localhost` to
> `C:\Windows\System32\drivers\etc\hosts`.

## The stack

`coreerp-verify/docker-compose.yml` defines an isolated stack:
- `coreerp-verify-bench` — Frappe v15 bench (port 8000 → host **8456**)
- `coreerp-verify-mariadb` — MariaDB 11.8 (db root password `123`)
- `coreerp-verify-redis-cache`, `coreerp-verify-redis-queue`

Site: `coreerp.localhost`. Apps installed: `frappe`, `coreerp`, `medicare`.

## Start / stop

```bash
# bring the stack up (from the coreerp-verify folder)
cd "/path/to/New folder/coreerp-verify" && docker compose up -d

# start the web server (the desk/portal)
docker exec -d coreerp-verify-bench bash -lc \
  "cd /home/frappe/frappe-bench && exec bench --site coreerp.localhost serve --port 8000 > /tmp/web.log 2>&1"

# stop the web server
docker exec coreerp-verify-bench bash -lc "pkill -f 'bench.*serve'"

# tear the whole stack down (KEEPS data in named volumes)
docker compose down
# tear down AND wipe all data (full reset)
docker compose down -v
```

The `bench serve` dev server is single-process; if the container restarts, re-run the
start command above. (For a long-lived setup, use `bench setup supervisor` instead.)

## The setup-wizard loop (fixed) — escape hatch

A site with **no ERPNext** could loop on `/app/setup-wizard`: during install Frappe sets
the desk home-page default to `setup-wizard`, and `is_setup_complete()` only inspects the
`frappe`/`erpnext` apps. If the wizard is bypassed, that default sticks and the desk loops.

CoreERP now heals this in `after_migrate` (`coreerp.setup.install.heal_setup_wizard_loop`),
which resets the home page to `Workspaces` **once setup is actually complete**. The normal
wizard still runs on a fresh site.

If you ever see the loop, force-complete setup and refresh:

```bash
docker exec coreerp-verify-bench bash -lc \
  "cd /home/frappe/frappe-bench && bench --site coreerp.localhost execute coreerp.setup.install.mark_setup_complete && bench --site coreerp.localhost clear-cache"
docker exec coreerp-verify-bench bash -lc "pkill -f 'bench.*serve'"
docker exec -d coreerp-verify-bench bash -lc \
  "cd /home/frappe/frappe-bench && exec bench --site coreerp.localhost serve --port 8000 > /tmp/web.log 2>&1"
```

Then hard-refresh the browser (Ctrl+Shift+R) or use an Incognito window — a normal refresh
keeps the stale cached `frappe.boot` and looks like the loop "sped up" rather than cleared.

## Common bench commands

```bash
D="docker exec coreerp-verify-bench bash -lc"
$D "cd /home/frappe/frappe-bench && bench --site coreerp.localhost migrate"
$D "cd /home/frappe/frappe-bench && bench --site coreerp.localhost clear-cache"
$D "cd /home/frappe/frappe-bench && bench build --app coreerp"
$D "cd /home/frappe/frappe-bench && bench --site coreerp.localhost console"
# run the smoke tests
$D "cd /home/frappe/frappe-bench/sites && ../env/bin/python -c \"import frappe; frappe.init(site='coreerp.localhost'); frappe.connect(); import coreerp.tests.smoke as s; s.run()\""
$D "cd /home/frappe/frappe-bench/sites && ../env/bin/python -c \"import frappe; frappe.init(site='coreerp.localhost'); frappe.connect(); import medicare.tests.smoke as s; s.run()\""
```
