# Migrating a Project off ERPNext onto CoreERP — Guide for Claude Code

> **This is a prompt/playbook for Claude Code to run inside ONE project at a time.**
> It is **audit-first** and **gated**: nothing destructive happens until the audit is
> shown to the user and they explicitly approve. ERPNext master data (Customer, Supplier,
> Company) is migrated into CoreERP **before** ERPNext is removed.

---

## 📋 COPY-PASTE THIS PROMPT TO CLAUDE CODE

> Paste the block below into Claude Code from inside the project you want to migrate.
> Fill in the two `<...>` placeholders first.

```text
You are migrating THIS project off ERPNext onto CoreERP. Follow the guide in
MIGRATE-OFF-ERPNEXT.md EXACTLY, phase by phase, top to bottom. Do not improvise an
alternative approach.

Environment:
- How to run bench: <"inside the frappe_docker devcontainer at /workspace/development/frappe-bench" OR "from host: docker exec <devcontainer>-frappe-1 bash -lc 'cd /workspace/development/frappe-bench && bench ...'">
- Site to migrate: <e.g. mysite.localhost>
- CoreERP source: bench get-app https://github.com/zopeeeeee/coreerp.git

NON-NEGOTIABLE RULES (from the guide's "Read this first"):
1. This is destructive and irreversible without backups. Take a backup
   (bench backup --with-files) in Phase 0 and again immediately before Phase 5.
   Never skip a backup.
2. Do NOT run `uninstall-app erpnext`, `remove-app erpnext`, or `drop-site` until I
   have replied "yes" in this chat AFTER you show me the audit. There are TWO approval
   gates (GATE 1 after the audit, GATE 2 after rewiring). Stop and wait for my "yes" at
   each gate. Treat any other reply as "no".
3. Run the Phase 1 AUDIT first (read-only). If the audit finds ANY ERPNext *transaction*
   data (GL Entry, Stock Ledger Entry, Sales/Purchase Invoice, Sales/Purchase Order,
   Stock Entry, Delivery Note, Payment Entry, Work Order, BOM with rows > 0), STOP and
   tell me this project genuinely uses ERPNext — do not migrate or delete anything.
4. Migrate masters BEFORE removing ERPNext: Company -> CoreERP Organization (direct), and
   Customer/Supplier -> a party doctype in MY app (CoreERP's slim core has no Client/Vendor).
   Keep the old->new name map and use it to repoint existing records.
5. Work on ONE site at a time. Do not batch across sites.
6. After every phase, give me a short status: what you ran, what you found, what's next.
   Use a todo list to track the phases.
7. If anything fails, STOP, show me the error, and propose the rollback (bench restore)
   rather than pushing forward.

Start now with Phase 0 (snapshot & backup), then Phase 1 (audit), then PAUSE at GATE 1
and show me the audit report before doing anything else.
```

---

## ⚠️ Read this first (Claude Code: obey these rules)

1. **NEVER run `uninstall-app erpnext` or `drop-site` without an explicit "yes" from the
   user in THIS session, after showing them the audit.** Uninstalling ERPNext drops all
   ERPNext tables — the data is irreversible without a backup.
2. **Always take a backup before any destructive step** (`bench backup --with-files`).
3. **Do the audit and migration per-site**, one at a time. Don't batch-delete across sites.
4. **If the audit finds accounting/stock/manufacturing *transactions*** (GL Entry, Stock
   Ledger Entry, Sales Invoice with data, Work Order, etc.), STOP and tell the user — that
   project genuinely uses ERPNext and is NOT a candidate for simple removal.
5. Treat "the user said they don't need ERPNext" as a hypothesis to **prove**, not a fact.

---

## Inputs Claude Code should establish

- `BENCH` — path to the bench (frappe_docker devcontainer: `/workspace/development/frappe-bench`).
- `SITE` — the site being migrated (run `bench --site all list-apps` to enumerate).
- `APPS` — the custom app(s) in this project that should survive (everything except `erpnext`).
- How CoreERP will be obtained: `bench get-app https://github.com/zopeeeeee/coreerp.git`.

Define a runner so commands are consistent (adapt to local vs docker):
```bash
# inside the frappe_docker devcontainer:
B() { cd /workspace/development/frappe-bench && bench "$@"; }
# OR from the host, exec-ing into the devcontainer:
# B() { docker exec <devcontainer>-frappe-1 bash -lc "cd /workspace/development/frappe-bench && bench $*"; }
```

---

## PHASE 0 — Snapshot & safety

```bash
B --site "$SITE" list-apps                 # confirm erpnext is installed; note custom apps
B --site "$SITE" backup --with-files       # MANDATORY backup. Note the backup path.
```
Record the backup location in your report. Do not proceed without a successful backup.

---

## PHASE 1 — AUDIT (read-only, no changes)

Goal: prove whether this project actually depends on ERPNext, and exactly where.

### 1a. Source-level coupling (in each custom app repo)
```bash
# imports from erpnext
grep -rn "from erpnext\|import erpnext" apps/<your_app> --include="*.py" | grep -v "test_"
# hooks referencing erpnext
grep -n "erpnext" apps/<your_app>/<your_app>/hooks.py
# link fields / fetch_from pointing at ERPNext doctypes
grep -rn '"options": *"\(Customer\|Supplier\|Company\|Item\|Account\|Cost Center\|Warehouse\|Sales Invoice\|Purchase Invoice\|Sales Order\|Purchase Order\|Stock Entry\|Delivery Note\)"' apps/<your_app> --include="*.json"
grep -rn '"fetch_from"' apps/<your_app> --include="*.json" | grep -iE "customer|supplier|company|item|account"
# controllers subclassing ERPNext bases
grep -rn "AccountsController\|StockController\|SellingController\|BuyingController\|TransactionBase" apps/<your_app> --include="*.py"
```

### 1b. Data-level usage (on the live site) — run this script
```python
# B --site $SITE execute frappe.utils.execute_in_shell  (or via console / a temp module)
import frappe
ERP_MASTERS = ["Customer","Supplier","Company","Item","Account","Cost Center","Warehouse"]
ERP_TXN = ["GL Entry","Stock Ledger Entry","Sales Invoice","Purchase Invoice","Sales Order",
           "Purchase Order","Stock Entry","Delivery Note","Payment Entry","Work Order","BOM"]
print("=== MASTER record counts ===")
for dt in ERP_MASTERS:
    if frappe.db.table_exists(dt): print(f"  {dt}: {frappe.db.count(dt)}")
print("=== TRANSACTION record counts (if ANY > 0, this project REALLY uses ERPNext) ===")
for dt in ERP_TXN:
    if frappe.db.table_exists(dt):
        n = frappe.db.count(dt)
        if n: print(f"  {dt}: {n}  <-- has data")
# which of YOUR doctypes link to ERPNext doctypes?
print("=== your doctypes linking to ERPNext masters ===")
for df in frappe.get_all("DocField", filters={"fieldtype":"Link","options":["in",ERP_MASTERS]},
                         fields=["parent","fieldname","options"]):
    print(f"  {df.parent}.{df.fieldname} -> {df.options}")
# custom fields too
for cf in frappe.get_all("Custom Field", filters={"fieldtype":"Link","options":["in",ERP_MASTERS]},
                         fields=["dt","fieldname","options"]):
    print(f"  (custom) {cf.dt}.{cf.fieldname} -> {cf.options}")
```

### 1c. Produce an AUDIT REPORT and show the user
Summarize:
- Does any **transaction** doctype have data? → if yes: **STOP, not a removal candidate.**
- Which **master** doctypes have data, and how many records (migration scope).
- Every link field (yours + custom) pointing at an ERPNext doctype (these are the rewires).
- Every source coupling (imports, hooks, controller bases).

**GATE 1:** Present this report. Ask the user: *"Proceed to migrate masters and remove
ERPNext for this site? (yes/no)"* Do not continue without an explicit yes.

---

## PHASE 2 — Install CoreERP alongside ERPNext (non-destructive)

```bash
B get-app https://github.com/zopeeeeee/coreerp.git
B --site "$SITE" install-app coreerp
B --site "$SITE" migrate
```
ERPNext still installed at this point. CoreERP now provides Organization + tenancy +
universal masters (it does NOT provide Client/Vendor — define your party doctype in your app).

---

## PHASE 3 — Migrate master data

> **IMPORTANT — slim CoreERP scope.** CoreERP is a *slim universal core*: it provides
> **Organization** + universal masters (UOM, Territory, Department, …) but **NOT** Client,
> Vendor, Customer, or Supplier (those are domain-specific and were intentionally removed).
> So:
> - **Company → CoreERP `Organization`** (direct, CoreERP provides it).
> - **Customer / Supplier →** a **party doctype YOU define in your own app** (e.g. a generic
>   `Party`, or domain-specific `Student`/`Patient`/`Member`). CoreERP has no target for them.
>
> Decide your target party doctype BEFORE running this phase. If the audit shows Customer/
> Supplier are only used as plain link masters, the simplest target is a small `Party`
> doctype in your app with name + group + contact fields, linked to Organization.

Run only for masters the audit found in use. The script is **idempotent** and keeps an
old→new name map for the relink phase. Replace `MY_PARTY_DOCTYPE` with your app's doctype.

```python
import frappe, json
frappe.flags.in_migrate = True
name_map = {"Company": {}, "Customer": {}, "Supplier": {}}

MY_PARTY_DOCTYPE = "Party"   # <-- the doctype YOU created in your app (or Student/Patient/etc.)

# Company -> CoreERP Organization (CoreERP provides this)
if frappe.db.table_exists("Company"):
    for c in frappe.get_all("Company", fields=["name","company_name","abbr","default_currency","country"]):
        new = c.company_name or c.name
        if not frappe.db.exists("Organization", new):
            frappe.get_doc({"doctype":"Organization","organization_name":new,"abbr":c.abbr,
                            "default_currency":c.default_currency,"country":c.country}).insert(ignore_permissions=True)
        name_map["Company"][c.name] = new

# Customer -> YOUR app's party doctype (CoreERP has no Client). Adjust fields to your schema.
if frappe.db.table_exists("Customer") and frappe.db.exists("DocType", MY_PARTY_DOCTYPE):
    for c in frappe.get_all("Customer", fields=["name","customer_name","territory","tax_id"]):
        doc = frappe.get_doc({"doctype": MY_PARTY_DOCTYPE,
                              "party_name": c.customer_name or c.name,   # rename to your field
                              "party_role": "Customer",
                              "tax_id": c.tax_id}).insert(ignore_permissions=True)
        name_map["Customer"][c.name] = doc.name

# Supplier -> YOUR app's party doctype (same target or a separate one)
if frappe.db.table_exists("Supplier") and frappe.db.exists("DocType", MY_PARTY_DOCTYPE):
    for s in frappe.get_all("Supplier", fields=["name","supplier_name","country","tax_id"]):
        doc = frappe.get_doc({"doctype": MY_PARTY_DOCTYPE,
                              "party_name": s.supplier_name or s.name,
                              "party_role": "Supplier",
                              "tax_id": s.tax_id}).insert(ignore_permissions=True)
        name_map["Supplier"][s.name] = doc.name

frappe.db.commit()
frappe.cache().set_value("erpnext_migration_map", json.dumps(name_map))
print("migrated:", {k: len(v) for k,v in name_map.items()})
```

> If you do NOT need a party master at all (e.g. an internal tool), skip the Customer/
> Supplier blocks — just record which of YOUR doctypes link to them so Phase 4 can drop or
> repoint those fields.

> Contacts & Addresses are **Frappe-native** (not ERPNext) — they survive uninstall. They're
> linked via Dynamic Link; after relinking, re-point any `Dynamic Link.link_doctype` rows
> from `Customer`/`Supplier` to your new party doctype (or `Organization`).

---

## PHASE 4 — Rewire YOUR app to CoreERP

For each link field the audit found (`<DocType>.<field> -> Customer/Supplier/Company`):

### 4a. Change the field definition (in your app's doctype JSON)
`"options": "Company"` → `"options": "Organization"` (CoreERP provides it).
`"options": "Customer"` / `"Supplier"` → `"options": "<your party doctype>"` (the one you
created in Phase 3, e.g. `Party`/`Student`/`Patient`). Do this in source, then `bench migrate`.

### 4b. Repoint existing rows to the new names (data)
```python
import json, frappe
name_map = json.loads(frappe.cache().get_value("erpnext_migration_map"))
# Example for one field: MyDoctype.client previously held a Customer name
RELINKS = [
    # (doctype, fieldname, source_master)
    ("My Doctype", "client", "Customer"),
    ("My Doctype", "organization", "Company"),
]
for dt, fn, src in RELINKS:
    for row in frappe.get_all(dt, fields=["name", fn]):
        old = row.get(fn)
        if old and old in name_map.get(src, {}):
            frappe.db.set_value(dt, row.name, fn, name_map[src][old], update_modified=False)
frappe.db.commit()
print("relinked")
```

### 4c. Fix source coupling
- Replace `from erpnext...` imports with CoreERP equivalents or your own helpers.
- Re-parent controllers from `AccountsController/SellingController/TransactionBase` to
  `frappe.model.document.Document`.
- Remove `erpnext` from your app's `required_apps`; add `coreerp`.
- Move any logic bolted onto ERPNext's global `doc_events["*"]` into scoped events.
- Re-point `permission_query_conditions` for tenant scoping to
  `coreerp.organization.tenant.get_permission_query_conditions` (+ add an `organization`
  field — see NEW-APP-PLAYBOOK.md §6).

**GATE 2:** Re-run the PHASE 1b data script. Confirm **no** remaining link fields point at
ERPNext masters and your app loads. Show the user. Ask: *"Audit clean — proceed to remove
ERPNext? (yes/no)"*

---

## PHASE 5 — Remove ERPNext (DESTRUCTIVE — only after GATE 2 yes)

```bash
B --site "$SITE" backup --with-files          # second backup, right before deletion
B --site "$SITE" uninstall-app erpnext --yes  # drops erpnext doctypes/tables for this site
# also remove from the bench if no other site uses it:
B --site all list-apps | grep -i erpnext || (cd "$BENCH" && bench remove-app erpnext)
# clean residue
B --site "$SITE" migrate
B --site "$SITE" clear-cache
B build
```

> `uninstall-app` removes ERPNext from THIS site. `remove-app` removes the app from the
> bench entirely — only do that if NO site still uses it.

---

## PHASE 6 — Verify (mirror the CoreERP checklist)

```bash
B --site "$SITE" migrate          # clean, no missing-module errors
B --site "$SITE" doctor || true
```
Then live-verify:
- Login + desk loads (no setup-wizard loop — CoreERP heals it).
- Your app's key doctypes open; the rewired link fields resolve to Organization / your party doctype.
- Records created pre-migration still open and show the migrated party.
- Reports / print formats that referenced Customer/Company still render (update any that
  hard-coded ERPNext fieldnames).
- Run your app's smoke test (see NEW-APP-PLAYBOOK.md §10).
- `grep -rn "erpnext" apps/<your_app>` returns nothing meaningful.

**Report to user:** what was migrated (counts), what was rewired, backups taken, and the
final verification results. Note any reports/fixtures that still need manual attention.

---

## Rollback

If anything goes wrong before/after PHASE 5:
```bash
B --site "$SITE" restore <backup-sql-from-phase-0-or-5> --with-files
```
Because masters were migrated and ERPNext only removed after GATE 2, the common failure
modes (a missed link field, a report referencing a deleted field) are caught at GATE 2 or
fixed forward — but the backup is the guaranteed escape hatch.

---

## Decision summary (the gate logic in one place)

```
Audit (Phase 1)
 ├─ ERPNext TRANSACTION data present?  ── yes ──▶ STOP. Project needs ERPNext. Do not remove.
 │                                      ── no ──▶ continue
 ├─ Masters in use?  ── yes ──▶ migrate (Phase 3) + rewire (Phase 4)
 │                    ── no  ──▶ skip to rewire-source-only
 └─ GATE 1 (user yes) ▶ install coreerp ▶ migrate masters ▶ rewire ▶ GATE 2 (user yes)
                                                                       ▶ backup ▶ uninstall erpnext ▶ verify
```
