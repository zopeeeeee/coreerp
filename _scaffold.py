"""One-shot scaffolder for CoreERP simple master doctypes.

Generates valid Frappe doctype JSON + a minimal controller for the straightforward
masters. Complex doctypes (Client, Vendor, Project, Task, Timesheet, Ticket, SLA,
Lead, Opportunity) are hand-authored separately.

Run from the coreerp repo root:  python _scaffold.py
This script is a build tool; it is NOT shipped/imported at runtime.
"""

import json
import os

BASE = os.path.join(os.path.dirname(__file__), "coreerp")
CREATION = "2026-01-01 00:00:00"


def field(fieldname, fieldtype, label, **kw):
	f = {"fieldname": fieldname, "fieldtype": fieldtype, "label": label}
	f.update(kw)
	return f


def perms(roles):
	out = []
	for role, level in roles:
		base = {"read": 1, "report": 1, "email": 1, "print": 1, "role": role}
		if level == "rw":
			base.update({"create": 1, "write": 1, "delete": 1, "export": 1, "share": 1})
		out.append(base)
	return out


def doctype(name, module, fields, field_order, *, autoname=None, naming_rule=None,
            is_tree=False, parent_field=None, child_table=False, search_fields=None,
            roles=None, icon="fa fa-file", title_field=None, track_changes=True):
	dt = {
		"actions": [],
		"allow_rename": 1,
		"creation": CREATION,
		"doctype": "DocType",
		"engine": "InnoDB",
		"field_order": field_order,
		"fields": fields,
		"icon": icon,
		"links": [],
		"modified": CREATION,
		"modified_by": "Administrator",
		"module": module,
		"name": name,
		"owner": "Administrator",
		"permissions": perms(roles or [("System Manager", "rw")]),
		"sort_field": "creation",
		"sort_order": "DESC",
		"states": [],
	}
	if autoname:
		dt["autoname"] = autoname
	if naming_rule:
		dt["naming_rule"] = naming_rule
	if is_tree:
		dt["is_tree"] = 1
		dt["nsm_parent_field"] = parent_field
	if child_table:
		dt["istable"] = 1
		dt.pop("permissions", None)
	else:
		dt["track_changes"] = 1 if track_changes else 0
		dt["show_name_in_global_search"] = 1
	if search_fields:
		dt["search_fields"] = search_fields
	if title_field:
		dt["title_field"] = title_field
	return dt


def write(module_dir, dtname, dt, controller_body=None, base_class="Document"):
	folder = dtname.lower().replace(" ", "_")
	path = os.path.join(BASE, module_dir, "doctype", folder)
	os.makedirs(path, exist_ok=True)
	open(os.path.join(path, "__init__.py"), "w").close()
	with open(os.path.join(path, f"{folder}.json"), "w", newline="\n") as fh:
		json.dump(dt, fh, indent=1)
		fh.write("\n")
	cls = dtname.replace(" ", "")
	if controller_body is None:
		if base_class == "NestedSet":
			imp = "from frappe.utils.nestedset import NestedSet"
			controller_body = f"\tpass\n"
		else:
			imp = "from frappe.model.document import Document"
			controller_body = "\tpass\n"
	else:
		imp = "from frappe.model.document import Document"
	header = (
		"# Copyright (c) 2026, CoreERP Contributors and contributors\n"
		"# For license information, please see license.txt\n\n"
		"import frappe\n"
		"from frappe import _\n"
		f"{imp}\n\n\n"
		f"class {cls}({base_class}):\n"
	)
	with open(os.path.join(path, f"{folder}.py"), "w", newline="\n") as fh:
		fh.write(header + controller_body)
	print(f"  wrote {module_dir}/doctype/{folder}")


# Shared role sets
ADMIN = [("System Manager", "rw"), ("Organization Manager", "rw")]
CRM = [("System Manager", "rw"), ("CRM Manager", "rw"), ("CRM User", "rw")]
PROJ = [("System Manager", "rw"), ("Project Manager", "rw"), ("Project Member", "rw")]
SVC = [("System Manager", "rw"), ("Service Manager", "rw"), ("Service Agent", "rw")]
HR = [("System Manager", "rw"), ("HR Basic User", "rw")]


def org_field():
	return field("organization", "Link", "Organization", options="Organization")


# ---------------------------------------------------------------------------
# COMMON masters
# ---------------------------------------------------------------------------
def build_common():
	write("common", "UOM",
		doctype("UOM", "Common",
			[field("uom_name", "Data", "UOM Name", reqd=1, unique=1, in_list_view=1),
			 field("enabled", "Check", "Enabled", default="1"),
			 field("must_be_whole_number", "Check", "Must be Whole Number")],
			["uom_name", "enabled", "must_be_whole_number"],
			autoname="field:uom_name", naming_rule="By fieldname",
			roles=ADMIN, icon="fa fa-balance-scale"))

	write("common", "UOM Conversion Factor",
		doctype("UOM Conversion Factor", "Common",
			[field("category", "Data", "Category"),
			 field("from_uom", "Link", "From UOM", options="UOM", reqd=1, in_list_view=1),
			 field("to_uom", "Link", "To UOM", options="UOM", reqd=1, in_list_view=1),
			 field("value", "Float", "Value", reqd=1, in_list_view=1)],
			["category", "from_uom", "to_uom", "value"],
			roles=ADMIN, icon="fa fa-exchange"))

	write("common", "Territory",
		doctype("Territory", "Common",
			[field("territory_name", "Data", "Territory Name", reqd=1, unique=1, in_list_view=1),
			 field("is_group", "Check", "Is Group"),
			 field("parent_territory", "Link", "Parent Territory", options="Territory"),
			 field("lft", "Int", "lft", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
			 field("rgt", "Int", "rgt", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
			 field("old_parent", "Data", "Old Parent", hidden=1, no_copy=1, print_hide=1)],
			["territory_name", "is_group", "parent_territory", "lft", "rgt", "old_parent"],
			autoname="field:territory_name", naming_rule="By fieldname",
			is_tree=True, parent_field="parent_territory",
			roles=ADMIN, icon="fa fa-map-marker"),
		base_class="NestedSet")

	write("common", "Brand",
		doctype("Brand", "Common",
			[field("brand", "Data", "Brand", reqd=1, unique=1, in_list_view=1),
			 field("description", "Text", "Description"),
			 field("image", "Attach Image", "Image", hidden=1)],
			["brand", "description", "image"],
			autoname="field:brand", naming_rule="By fieldname",
			roles=ADMIN, icon="fa fa-certificate"))

	write("common", "Terms and Conditions",
		doctype("Terms and Conditions", "Common",
			[field("title", "Data", "Title", reqd=1, unique=1, in_list_view=1),
			 field("disabled", "Check", "Disabled"),
			 field("terms", "Text Editor", "Terms and Conditions")],
			["title", "disabled", "terms"],
			autoname="field:title", naming_rule="By fieldname",
			roles=ADMIN, icon="fa fa-file-text"))


# ---------------------------------------------------------------------------
# PARTIES
# ---------------------------------------------------------------------------
def build_parties():
	write("parties", "Party Type",
		doctype("Party Type", "Parties",
			[field("party_type", "Data", "Party Type", reqd=1, unique=1, in_list_view=1)],
			["party_type"],
			autoname="field:party_type", naming_rule="By fieldname",
			roles=ADMIN, icon="fa fa-users"))

	for grp, parent in [("Client Group", "parent_client_group"), ("Vendor Group", "parent_vendor_group")]:
		fn = grp.lower().replace(" ", "_") + "_name"
		write("parties", grp,
			doctype(grp, "Parties",
				[field(fn, "Data", grp + " Name", reqd=1, unique=1, in_list_view=1),
				 field("is_group", "Check", "Is Group"),
				 field(parent, "Link", "Parent " + grp, options=grp),
				 field("lft", "Int", "lft", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
				 field("rgt", "Int", "rgt", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
				 field("old_parent", "Data", "Old Parent", hidden=1, no_copy=1, print_hide=1)],
				[fn, "is_group", parent, "lft", "rgt", "old_parent"],
				autoname="field:" + fn, naming_rule="By fieldname",
				is_tree=True, parent_field=parent,
				roles=ADMIN, icon="fa fa-sitemap"),
			base_class="NestedSet")


# ---------------------------------------------------------------------------
# HR BASICS
# ---------------------------------------------------------------------------
def build_hr():
	write("hr_basics", "Designation",
		doctype("Designation", "HR Basics",
			[field("designation_name", "Data", "Designation", reqd=1, unique=1, in_list_view=1),
			 field("description", "Text", "Description")],
			["designation_name", "description"],
			autoname="field:designation_name", naming_rule="By fieldname",
			roles=HR, icon="fa fa-id-badge"))

	write("hr_basics", "Branch",
		doctype("Branch", "HR Basics",
			[field("branch", "Data", "Branch", reqd=1, unique=1, in_list_view=1),
			 org_field()],
			["branch", "organization"],
			autoname="field:branch", naming_rule="By fieldname",
			roles=HR, icon="fa fa-code-fork"))

	write("hr_basics", "Department",
		doctype("Department", "HR Basics",
			[field("department_name", "Data", "Department", reqd=1, in_list_view=1),
			 org_field(),
			 field("is_group", "Check", "Is Group"),
			 field("parent_department", "Link", "Parent Department", options="Department"),
			 field("lft", "Int", "lft", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
			 field("rgt", "Int", "rgt", hidden=1, read_only=1, no_copy=1, print_hide=1, search_index=1),
			 field("old_parent", "Data", "Old Parent", hidden=1, no_copy=1, print_hide=1)],
			["department_name", "organization", "is_group", "parent_department", "lft", "rgt", "old_parent"],
			is_tree=True, parent_field="parent_department",
			roles=HR, icon="fa fa-building-o"),
		base_class="NestedSet")

	write("hr_basics", "Holiday",
		doctype("Holiday", "HR Basics",
			[field("holiday_date", "Date", "Date", reqd=1, in_list_view=1),
			 field("description", "Small Text", "Description", reqd=1, in_list_view=1),
			 field("weekly_off", "Check", "Weekly Off")],
			["holiday_date", "description", "weekly_off"],
			child_table=True, icon="fa fa-calendar"))

	write("hr_basics", "Holiday List",
		doctype("Holiday List", "HR Basics",
			[field("holiday_list_name", "Data", "Name", reqd=1, unique=1, in_list_view=1),
			 org_field(),
			 field("from_date", "Date", "From Date", reqd=1),
			 field("to_date", "Date", "To Date", reqd=1),
			 field("total_holidays", "Int", "Total Holidays", read_only=1),
			 field("holidays_section", "Section Break", "Holidays"),
			 field("holidays", "Table", "Holidays", options="Holiday")],
			["holiday_list_name", "organization", "from_date", "to_date", "total_holidays",
			 "holidays_section", "holidays"],
			autoname="field:holiday_list_name", naming_rule="By fieldname",
			roles=HR, icon="fa fa-calendar"))

	emp_fields = [
		field("employee_name", "Data", "Full Name", reqd=1, in_list_view=1),
		org_field(),
		field("user", "Link", "User", options="User"),
		field("status", "Select", "Status", options="Active\nInactive\nLeft", default="Active", in_list_view=1),
		field("col_break_1", "Column Break", ""),
		field("department", "Link", "Department", options="Department"),
		field("designation", "Link", "Designation", options="Designation"),
		field("branch", "Link", "Branch", options="Branch"),
		field("reports_to", "Link", "Reports To", options="Employee Profile"),
		field("section_personal", "Section Break", "Personal"),
		field("gender", "Link", "Gender", options="Gender"),
		field("date_of_birth", "Date", "Date of Birth"),
		field("date_of_joining", "Date", "Date of Joining"),
		field("col_break_2", "Column Break", ""),
		field("personal_email", "Data", "Personal Email", options="Email"),
		field("mobile", "Data", "Mobile", options="Phone"),
		field("holiday_list", "Link", "Holiday List", options="Holiday List"),
	]
	write("hr_basics", "Employee Profile",
		doctype("Employee Profile", "HR Basics", emp_fields,
			[f["fieldname"] for f in emp_fields],
			autoname="naming_series:", search_fields="employee_name,department,designation",
			roles=HR, icon="fa fa-user", title_field="employee_name"))


# ---------------------------------------------------------------------------
# ENGAGEMENT (CRM) — masters; Lead/Opportunity hand-authored if complex
# ---------------------------------------------------------------------------
def build_engagement_masters():
	write("engagement", "Lead Source",
		doctype("Lead Source", "Engagement",
			[field("source_name", "Data", "Source Name", reqd=1, unique=1, in_list_view=1),
			 field("details", "Text", "Details")],
			["source_name", "details"],
			autoname="field:source_name", naming_rule="By fieldname",
			roles=CRM, icon="fa fa-filter"))

	write("engagement", "Market Segment",
		doctype("Market Segment", "Engagement",
			[field("market_segment", "Data", "Market Segment", reqd=1, unique=1, in_list_view=1)],
			["market_segment"],
			autoname="field:market_segment", naming_rule="By fieldname",
			roles=CRM, icon="fa fa-pie-chart"))

	write("engagement", "Campaign",
		doctype("Campaign", "Engagement",
			[field("campaign_name", "Data", "Campaign Name", reqd=1, unique=1, in_list_view=1),
			 org_field(),
			 field("description", "Text Editor", "Description"),
			 field("col", "Column Break", ""),
			 field("start_date", "Date", "Start Date"),
			 field("end_date", "Date", "End Date")],
			["campaign_name", "organization", "description", "col", "start_date", "end_date"],
			autoname="field:campaign_name", naming_rule="By fieldname",
			roles=CRM, icon="fa fa-bullhorn"))

	write("engagement", "Opportunity Item",
		doctype("Opportunity Item", "Engagement",
			[field("item_name", "Data", "Item / Service", reqd=1, in_list_view=1),
			 field("description", "Small Text", "Description"),
			 field("qty", "Float", "Qty", default="1", in_list_view=1),
			 field("uom", "Link", "UOM", options="UOM"),
			 field("rate", "Currency", "Rate", in_list_view=1),
			 field("amount", "Currency", "Amount", read_only=1, in_list_view=1)],
			["item_name", "description", "qty", "uom", "rate", "amount"],
			child_table=True, icon="fa fa-list"))


# ---------------------------------------------------------------------------
# PROJECTS masters
# ---------------------------------------------------------------------------
def build_projects_masters():
	for nm, icon in [("Project Type", "fa fa-folder"), ("Task Type", "fa fa-tasks"),
	                 ("Activity Type", "fa fa-clock-o")]:
		fn = nm.lower().replace(" ", "_")
		write("projects", nm,
			doctype(nm, "Projects",
				[field(fn, "Data", nm, reqd=1, unique=1, in_list_view=1),
				 field("description", "Small Text", "Description")],
				[fn, "description"],
				autoname="field:" + fn, naming_rule="By fieldname",
				roles=PROJ, icon=icon))

	write("projects", "Project User",
		doctype("Project User", "Projects",
			[field("user", "Link", "User", options="User", reqd=1, in_list_view=1),
			 field("email", "Data", "Email", read_only=1),
			 field("view_attachments", "Check", "View Attachments")],
			["user", "email", "view_attachments"],
			child_table=True, icon="fa fa-user"))

	write("projects", "Timesheet Detail",
		doctype("Timesheet Detail", "Projects",
			[field("activity_type", "Link", "Activity Type", options="Activity Type"),
			 field("task", "Link", "Task", options="Task"),
			 field("project", "Link", "Project", options="Project"),
			 field("from_time", "Datetime", "From Time", in_list_view=1),
			 field("to_time", "Datetime", "To Time", in_list_view=1),
			 field("hours", "Float", "Hours", in_list_view=1),
			 field("description", "Small Text", "Description")],
			["activity_type", "task", "project", "from_time", "to_time", "hours", "description"],
			child_table=True, icon="fa fa-clock-o"))


# ---------------------------------------------------------------------------
# SERVICE masters
# ---------------------------------------------------------------------------
def build_service_masters():
	for nm, icon in [("Ticket Priority", "fa fa-flag"), ("Ticket Type", "fa fa-tag")]:
		fn = nm.lower().replace(" ", "_")
		write("service", nm,
			doctype(nm, "Service",
				[field(fn, "Data", nm, reqd=1, unique=1, in_list_view=1),
				 field("description", "Small Text", "Description")],
				[fn, "description"],
				autoname="field:" + fn, naming_rule="By fieldname",
				roles=SVC, icon=icon))

	write("service", "SLA Priority",
		doctype("SLA Priority", "Service",
			[field("priority", "Link", "Priority", options="Ticket Priority", reqd=1, in_list_view=1),
			 field("response_time", "Duration", "Response Time", in_list_view=1),
			 field("resolution_time", "Duration", "Resolution Time", in_list_view=1),
			 field("default_priority", "Check", "Default Priority")],
			["priority", "response_time", "resolution_time", "default_priority"],
			child_table=True, icon="fa fa-flag"))


if __name__ == "__main__":
	print("Scaffolding CoreERP simple doctypes...")
	build_common()
	build_parties()
	build_hr()
	build_engagement_masters()
	build_projects_masters()
	build_service_masters()
	print("Done.")
