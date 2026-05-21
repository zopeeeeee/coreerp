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

## Runtime validation (run on your bench after `install-app`)
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
