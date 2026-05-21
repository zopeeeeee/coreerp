# CoreERP — Portal System Guide

CoreERP reuses Frappe's complete website/portal stack and ships a minimal, generic portal.
Source: `coreerp/hooks.py` (website hooks), `coreerp/organization/tenant.py` (portal perms).

## What you get from Frappe (Layer 0)
Path resolver + router · WebsiteGenerator · **Web Form** (dynamic forms over any doctype) ·
**Web Page** (CMS) · Web Template/Theme · **Portal Settings / Portal Menu Item** · Help Article
(KB) · file serving (public/private) · REST API · realtime (Socket.IO) · login/signup/sessions.
None of this is re-implemented — CoreERP just configures it.

## What CoreERP ships
| Piece | Value |
|---|---|
| `website_route_rules` | `/projects → Project`, `/tickets → Ticket` |
| `standard_portal_menu_items` | Projects, Tickets (role: **Portal Client**) |
| `has_website_permission` | tenant-aware: portal client sees own-org / own records |
| Portal default role | `Portal Client` (set in install + CoreERP Settings) |

No `/orders`, `/invoices`, `/boms` (those are ERPNext's; excluded by design).

## Enabling portal users
1. Create the user as **Website User** (User → user_type).
2. Assign role **Portal Client**.
3. (Optional) Give a `Organization` User Permission to scope their visibility.
4. They log in at `/login` and land on the portal home (`Portal Settings → default_portal_home`).

## Exposing a doctype on the portal
Add a Web Form (fixture) over the doctype, plus a Portal Menu Item:

```python
# in your app hooks.py
standard_portal_menu_items = [
    {"title": "My Requests", "route": "/requests",
     "reference_doctype": "Service Request", "role": "Portal Client"},
]
```
For self-service forms, ship a **Web Form** with `login_required`, `apply_document_permissions`,
and `show_list` so users see only their own submissions (combined with `if_owner` DocPerms).

## Permission model on the portal
- `Ticket` DocPerm grants Portal Client `if_owner` read/write/create → a client sees only their own
  tickets.
- `has_website_permission` (`coreerp.organization.tenant.has_website_permission`) additionally
  scopes by organization when tenant isolation is on.

## Branding & content
Use Frappe's **Website Settings** (logo, navbar, footer, robots), **Website Theme** (colors/SCSS),
**Web Page** for marketing/landing pages, **Help Article** for a knowledge base. CoreERP doesn't
override these — set them per site.

## API for a custom SPA portal
Use `/api/method/coreerp.api.platform.whoami` and `.platform_summary` for bootstrap, then standard
`/api/resource/<doctype>` REST endpoints. Auth via API key or OAuth (see RBAC-guide.md).
Realtime updates via Frappe's Socket.IO rooms.
