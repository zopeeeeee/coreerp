# CoreERP — Migration Guide (from ERPNext)

For teams moving a custom app off ERPNext onto the neutral CoreERP base.

## When CoreERP is the right move
- Your app never posts ledgers/stock (you used ERPNext only for Customer/Company/Project/etc.).
- You want a clean upgrade path and no manufacturing/accounting baggage.

If you genuinely need accounting/stock, keep them as **plugins** on CoreERP (or stay on ERPNext for
that product).

## Field/doctype mapping

| ERPNext | CoreERP | Notes |
|---|---|---|
| Company | Organization | No account-default fields. |
| Customer | Client | No PartyAccount/credit limit. |
| Supplier | Vendor | No PartyAccount. |
| Customer Group / Supplier Group | Client Group / Vendor Group | Trees, no `accounts`. |
| Employee | Employee Profile | HR-basics only (no payroll). |
| Issue | Ticket | SLA preserved. |
| Issue Priority/Type | Ticket Priority/Type | — |
| Project / Task / Timesheet | same names | Billing/costing fields removed. |
| Lead / Opportunity | same names | Re-parented to `Document`; no selling/tax. |
| Item (as master) | (your Product doctype) or generic Dynamic Link | Stock not included. |

## Steps
1. **Inventory coupling**: `grep -rn "from erpnext" your_app/` — each is a thing to replace.
2. **Stand up CoreERP** on a fresh site (`install-app coreerp`).
3. **Re-point** `required_apps` → `["frappe", "coreerp"]`; rename link fields per the table above.
4. **Re-parent controllers** from `AccountsController/SellingController/TransactionBase` →
   `frappe.model.document.Document` (+ your own mixins).
5. **Data migration**: export ERPNext masters → Data Import into CoreERP doctypes, or write a
   one-time patch transforming an existing DB.
6. **Tenant scoping**: create User Permissions on `Organization`; register your doctypes via
   `coreerp_extensions["tenant_doctypes"]`.
7. **Hooks**: move any `doc_events["*"]` logic to scoped events; recreate Workflows/Notifications/
   Print Formats as fixtures.
8. **Verify** (see repo-root `VALIDATION-CHECKLIST.md`): migrate, login, portal, workflow, email,
   reports, permissions, API, scheduler.

## Effort
- No ledgers used → low (renames + dependency swap).
- Masters only → medium (remodel 3–5 + data migration).
- Posts ledgers/stock → high (build/keep finance+inventory plugins).
