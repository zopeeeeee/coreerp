# CoreERP — How to Create a New Module

Whether you're adding a module **inside** CoreERP (rare — keep it neutral) or, more commonly, in a
**downstream app**, the mechanics are the same.

## 1. Register the module
Add the module name to your app's `modules.txt` (one per line). On `bench migrate` Frappe creates a
**Module Def**. The module name maps to a snake_case folder.

```
# myapp/myapp/modules.txt
Admissions
```
→ folder `myapp/myapp/admissions/`

## 2. Scaffold the doctype
```bash
bench --site mysite make-doctype "Admission"   # or create via Desk in developer mode
```
This produces `admissions/doctype/admission/{admission.json, admission.py, __init__.py}`.

Or follow CoreERP's pattern: a `.json` (schema), a `.py` controller subclassing
`frappe.model.document.Document`, and an empty `__init__.py`.

## 3. Wire dependencies cleanly
- Link to CoreERP masters (`Client`, `Organization`, `Project`) via Link fields.
- Add an `organization` field if the doctype is tenant-scoped.
- Keep the controller free of cross-domain imports.

## 4. Make it tenant-safe (if applicable)
```python
# myapp/hooks.py
coreerp_extensions = {"tenant_doctypes": ["Admission"]}
permission_query_conditions = {
    "Admission": "coreerp.organization.tenant.get_permission_query_conditions",
}
```

## 5. Add UX
- A **Workspace** card/links JSON (`<module>/workspace/<name>/<name>.json`).
- **Reports** (`<module>/report/...`), **Dashboard Charts**, **Number Cards** as fixtures.
- **Print Formats** and **Web Forms** for portal exposure.

## 6. Permissions & roles
Define roles in `DocPerm` (in the doctype JSON) and bundle them via a Role Profile fixture.
Reuse CoreERP roles where they fit (`Project Member`, `Service Agent`, `Portal Client`).

## 7. Events & jobs
Scoped `doc_events` and `scheduler_events` in your hooks.py. Never `"*"`.

## 8. Migrate & verify
```bash
bench --site mysite migrate
bench --site mysite console   # smoke-test creating a record
```

## Checklist
- [ ] module in modules.txt
- [ ] doctype JSON + controller + __init__.py
- [ ] links resolve (no dangling options)
- [ ] tenant field + registry entry (if scoped)
- [ ] roles/permissions set
- [ ] workspace + reports
- [ ] scoped hooks only
- [ ] migrate clean
