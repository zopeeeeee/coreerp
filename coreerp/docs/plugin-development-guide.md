# CoreERP — Plugin Development Guide

How to build an app **on top of** CoreERP (university_erp, hospital_erp, crm_pro, supportdesk,
or a finance plugin) and reuse the platform without forking it.

## 1. Create your app

```bash
bench new-app university_erp
# in university_erp/hooks.py:
required_apps = ["frappe", "coreerp"]
bench --site mysite install-app university_erp
```

Your app inherits **everything** from CoreERP + Frappe: auth, RBAC, workflow, portal, web forms,
REST, notifications, files, dashboards, reports, print, jobs, plus Organization/Client/Project/etc.

## 2. Add your own doctypes
Author them in your app's modules. Link to CoreERP masters freely:

```json
{ "fieldname": "client", "fieldtype": "Link", "options": "Client" }
{ "fieldname": "organization", "fieldtype": "Link", "options": "Organization" }
```

## 3. Make your doctypes tenant-safe
Add an `organization` Link field, then register it via the extension registry so it gets the same
tenant query filter:

```python
# university_erp/hooks.py
coreerp_extensions = {
    "tenant_doctypes": ["Admission", "Course Enrollment"],
}
# university_erp/hooks.py — and route their permissions through CoreERP's tenant module:
permission_query_conditions = {
    "Admission": "coreerp.organization.tenant.get_permission_query_conditions",
}
```

## 4. Extend CoreERP masters (instead of editing them)
Need a receivable account on Client? Ship a **Custom Field** as a fixture in your finance plugin:

```python
# finance/hooks.py
fixtures = [{"dt": "Custom Field", "filters": [["dt", "in", ["Client", "Organization"]]]}]
```
CoreERP stays neutral; your plugin adds the field only when installed. This is exactly how ERPNext
*should* have layered accounting.

## 5. The extension registry (`coreerp.core.extensions`)
Recognized kinds: `party_dashboards`, `tenant_doctypes`, `workspace_shortcuts`, `portal_items`,
`role_bundles`, `api_namespaces`, `setup_steps`.

Declarative (preferred) — in your hooks.py:
```python
coreerp_extensions = {
    "party_dashboards": ["university_erp.extend.client_dashboard"],
    "workspace_shortcuts": ["university_erp.extend.shortcuts"],
}
```
Imperative (dynamic) — in after_install/boot:
```python
from coreerp.core.extensions import register
register("portal_items", {"title": "My Courses", "route": "/courses", "role": "Portal Client"})
```
CoreERP consumes these at its extension points (e.g. `get_tenant_doctypes()`,
`run_extensions("party_dashboards", client)`).

## 6. Add scheduler / events
Use scoped `doc_events` and your own `scheduler_events` in your hooks.py. **Never** add a `"*"`
doc_event. Frappe merges hooks across apps.

## 7. Add portal pages / web forms
Ship Web Form / Web Page / Portal Menu Item records (fixtures) for your doctypes. Reuse CoreERP's
`Portal Client` role or define your own.

## Golden rules
- Depend downward (your app → coreerp → frappe). Never make CoreERP depend on you.
- Extend via Custom Field / fixtures / extension registry — don't modify CoreERP doctype JSON.
- Keep finance/stock/manufacturing in **separate** plugins, opt-in per product.
