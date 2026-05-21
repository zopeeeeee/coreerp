# CoreERP — Validation Checklist

## Static validation (done in this environment)
Run: `python _validate.py`

| Check | Result |
|---|---|
| All doctype JSON parses | ✅ 37 doctypes |
| Required keys present (name, module, fields, permissions) | ✅ |
| No real `erpnext` imports (AST scan) | ✅ 0 |
| No global `doc_events["*"]` | ✅ |
| All hooks-referenced functions resolve to real files | ✅ 18/18 |
| All Link/Table `options` targets exist (CoreERP or known Frappe) | ✅ no dangling links |
| All Python compiles (ast.parse) | ✅ |
| Controllers : JSON parity | ✅ 37 : 37 |

## Runtime validation — ✅ EXECUTED on a live Frappe v15 site

Verified in an isolated Docker stack (Frappe 15.105.0, MariaDB 11.8, Redis), site
`coreerp.localhost`. `bench install-app coreerp` + `bench migrate` succeeded and the
runtime smoke test (`coreerp/tests/smoke.py`) passed **13/13**:

| Live check | Result |
|---|---|
| `install-app coreerp` | ✅ "CoreERP: baseline platform installed." |
| `bench migrate` (idempotent, re-run twice) | ✅ no errors |
| 37 doctypes registered across 8 modules | ✅ |
| 10 roles + 4 role profiles + default Organization + Settings + Workspace | ✅ |
| 3 patches applied | ✅ |
| CRUD (Client/Project/Task/Ticket/Timesheet/Lead/Employee) | ✅ |
| doc_event: Task→Project % rollup = 50.0 | ✅ |
| doc_event: Ticket SLA response_by/resolution_by computed | ✅ |
| doc_event: Timesheet total_hours = 3.5 | ✅ |
| fetch_from: Task pulls org from Project | ✅ |
| Lead→Client conversion (whitelisted method) | ✅ |
| 4 scheduler jobs run without error | ✅ |
| Permissions: Service Agent reads Ticket, cannot create Organization | ✅ |
| Tenant isolation: user restricted to Beta Org sees only Beta Org clients | ✅ |
| API (token auth): whoami / platform_summary / list_modules return data | ✅ |
| HTTP: ping 200, /login 200, / 200, guest API 403 | ✅ |

**4 real bugs were found and fixed during live verification** (see BUILD-REPORT.md §Verification):
module name collision (`CoreERP`→folder mismatch, then `Core`→clashed with Frappe's Core
module → renamed to **Platform**), a duplicate `autoname` key on Employee Profile, the
`has_permission` hook signature (`doc=None` case), and the tenant `permission_query_conditions`
clause (table-qualified, no isolation-breaking `OR NULL`).

To reproduce: `cd frappe-bench/sites && ../env/bin/python -c "import frappe; \
frappe.init(site='coreerp.localhost'); frappe.connect(); import coreerp.tests.smoke as s; s.run()"`

## Runtime checklist (reference — to re-run on any bench)
These require a live site; checklist mirrors the brief's Phase 9.

```bash
SITE=mysite.localhost
bench --site $SITE migrate                              # [ ] no schema/patch errors
bench --site $SITE execute frappe.installer.install_app --args "['coreerp']"  # [ ] installs clean
bench --site $SITE list-apps                            # [ ] coreerp listed
```

- [ ] **Login** — Administrator + a CoreERP-role user can log in.
- [ ] **Desk loads** — CoreERP workspace renders; cards/links resolve.
- [ ] **CRUD** — create Organization, Client, Project, Task, Ticket, Lead, Opportunity.
- [ ] **Permissions** — log in as Project Member / Service Agent / Portal Client; verify scope.
- [ ] **Tenant isolation** — enable in Settings, add Organization User Permission, confirm filtering.
- [ ] **Workflow** — attach a Workflow to Ticket; transitions create Workflow Actions.
- [ ] **doc_events** — saving a Ticket runs `apply_sla` (response_by/resolution_by set);
      Timesheet `calculate_hours` totals; Task on_update rolls up Project %.
- [ ] **Scheduler** — `bench --site $SITE execute coreerp.service.doctype.ticket.ticket.auto_close_resolved_tickets`.
- [ ] **Email queue** — Notification fires; Email Queue populated.
- [ ] **Reports** — build a Report Builder report over Project/Ticket.
- [ ] **Portal** — Portal Client visits `/projects`, `/tickets`; sees own records only.
- [ ] **Website render** — portal pages return 200.
- [ ] **API auth** — `curl -H "Authorization: token KEY:SECRET" $SITE/api/method/coreerp.api.platform.whoami`.
- [ ] **Realtime** — list view live-updates on edit (Frappe Socket.IO).
- [ ] **Background jobs** — RQ workers process enqueued jobs.

## Acceptance criteria (from brief)
- [x] No broken imports (static).
- [x] No hidden ERPNext dependencies (AST scan = 0).
- [x] No missing patches (3 patches present + referenced).
- [x] No failing hooks (all 18 refs resolve).
- [x] No circular dependencies (clean DAG; trees are not cycles).
- [ ] Confirmed on a live bench (run the runtime checklist above).
