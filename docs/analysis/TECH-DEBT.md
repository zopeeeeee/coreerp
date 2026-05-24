# CoreERP — Technical Debt & Refactoring Opportunities

Honest accounting of what's incomplete or could be better. This is a v0.1 foundation; the
following are known gaps, not hidden ones.

## Technical debt

| # | Item | Impact | Notes |
|---|---|---|---|
| 1 | **Not run through `bench migrate` in this environment** | Medium | No bench/MariaDB/Redis available on the build machine. JSON/imports/links/hooks validated statically (37 doctypes, 0 errors). First real `bench install-app` may surface minor schema nits (e.g. a missing `naming_series` option, a label tweak). |
| 2 | `tenant.get_permission_query_conditions` returns a column-based clause | Medium | Works when the scoped doctype has an `organization` column (all 8 do). For a doctype without it, the clause would error — the registry (`tenant_doctypes`) assumes the column exists. Document this requirement for plugin authors (done in plugin guide). |
| 3 | No automated test suite yet | Medium | `_validate.py` covers static integrity; runtime unit tests (`test_*.py` per doctype) are TODO. |
| 4 | No JS bundle / client scripts | Low | `app_include_js` is commented out; forms use default desk behavior. Add `public/js/coreerp.bundle.js` when custom client UX is needed. |
| 5 | Setup wizard is minimal | Low | Two stages (org + defaults). Downstream apps extend via `setup_steps`. |
| 6 | Opportunity `currency`/amount has no FX conversion | Low | Intentional (no accounting). If multi-currency reporting is needed, a finance plugin should own it. |
| 7 | Employee Profile naming uses `format:EMP-{#####}` | Low | Simple counter; switch to naming series if org-prefixed IDs are wanted. |
| 8 | Portal pages are route stubs | Low | `/projects`, `/tickets` map to doctype list views; bespoke portal templates (Web Pages/Web Forms) are left to the product app. |
| 9 | Fixtures reference roles created in `install.py` | Low | Roles are created both imperatively (install) and as fixtures; on first export, dedupe to fixtures-only if preferred. |
| 10 | No CI config | Low | Add GitHub Actions running `_validate.py` + `bench` smoke test. |

## Refactoring opportunities

1. **Mixin library for cross-cutting behavior.** Provide opt-in mixins (`TenantScopedMixin`,
   `AssignableMixin`) so downstream doctypes get tenant field + query wiring by inheritance instead
   of manual hook registration — composition over ERPNext's controller-inheritance spine.
2. **Generic "Dimension" framework** as an optional module, so plugins (finance/projects) can add
   analytical dimensions without each re-inventing it (the clean version of ERPNext's accounting
   dimensions).
3. **Promote tenant isolation to a first-class toggle per doctype** via a Custom Field/Property
   instead of a hardcoded list in `extensions.get_tenant_doctypes()`.
4. **Extract a `coreerp.common.utils`** for shared helpers (exchange-rate stub, address/contact
   sync) so Client/Vendor/Lead don't repeat the primary-contact sync logic.
5. **Web Form fixtures** for portal self-service (ticket submission, project status) shipped with
   the app rather than left to each product.
6. **Number Cards + Dashboard Charts** as fixtures for the CoreERP workspace (currently links/cards
   only; no KPIs yet).
7. **Typed controllers** — add the Frappe auto-generated `# begin: auto-generated types` blocks
   (generated on first `bench migrate`) for IDE support.
8. **Split `core/extensions.py` heuristic** (`_looks_like_method`) — replace the name heuristic with
   explicit typing in the registry to avoid edge cases distinguishing method paths from literals.
