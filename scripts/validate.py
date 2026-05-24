"""Static validation for CoreERP (no bench/site required).

Checks:
  1. Every doctype JSON parses and has required keys.
  2. No `erpnext` imports anywhere in the app.
  3. No global `doc_events["*"]` in hooks.py.
  4. Every method referenced by hooks.py resolves to a real file + function.
  5. Every Link/Table `options` target is either a CoreERP doctype or a known
     Frappe-core doctype (i.e. no dangling links).
  6. Python files compile.
"""

import ast
import json
import os
import re
import sys

# repo-root/coreerp/  (this script lives in repo-root/scripts/)
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coreerp")
ERRORS = []
WARN = []

# Frappe-core doctypes CoreERP is allowed to link to (subset that we use).
FRAPPE_DOCTYPES = {
	"User", "Role", "Contact", "Address", "Currency", "Country", "Language",
	"Gender", "Salutation", "Module Def", "File", "Communication",
}


def find(pattern):
	out = []
	for dirpath, _dirs, files in os.walk(ROOT):
		for f in files:
			if re.search(pattern, f):
				out.append(os.path.join(dirpath, f))
	return out


def collect_doctypes():
	names = set()
	for jf in find(r"\.json$"):
		if os.sep + "doctype" + os.sep not in jf and os.sep + "workspace" + os.sep not in jf:
			continue
		try:
			data = json.load(open(jf, encoding="utf-8"))
		except Exception as e:
			ERRORS.append(f"JSON parse error: {jf}: {e}")
			continue
		if data.get("doctype") == "DocType":
			names.add(data["name"])
	return names


def check_json_and_links(known):
	for jf in find(r"\.json$"):
		if os.sep + "doctype" + os.sep not in jf:
			continue
		data = json.load(open(jf, encoding="utf-8"))
		if data.get("doctype") != "DocType":
			continue
		for key in ("name", "module", "fields", "permissions"):
			if key not in data and not (key == "permissions" and data.get("istable")):
				if key == "permissions" and data.get("issingle"):
					continue
				ERRORS.append(f"{data.get('name', jf)}: missing key '{key}'")
		for fld in data.get("fields", []):
			if fld.get("fieldtype") in ("Link", "Table", "Tree") and fld.get("options"):
				target = fld["options"]
				if target in ("opportunity_from",):  # dynamic link source field, ok
					continue
				if target not in known and target not in FRAPPE_DOCTYPES:
					WARN.append(f"{data['name']}.{fld['fieldname']} -> unknown link target '{target}'")


def check_no_erpnext():
	"""Flag real erpnext IMPORTS (AST-level), not mentions in docstrings/comments."""
	for pf in find(r"\.py$"):
		if os.path.basename(pf).startswith("_"):
			continue
		try:
			tree = ast.parse(open(pf, encoding="utf-8").read())
		except SyntaxError:
			continue  # reported by check_compiles
		for node in ast.walk(tree):
			if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("erpnext"):
				ERRORS.append(f"erpnext IMPORT in {pf}:{node.lineno}")
			if isinstance(node, ast.Import):
				for alias in node.names:
					if alias.name.startswith("erpnext"):
						ERRORS.append(f"erpnext IMPORT in {pf}:{node.lineno}")


def check_hooks():
	hooks_path = os.path.join(ROOT, "hooks.py")
	txt = open(hooks_path, encoding="utf-8").read()
	if re.search(r'doc_events\s*=\s*\{[^}]*"\*"', txt, re.DOTALL):
		# allow only if commented; we simply flag a literal "*" key
		if re.search(r'^\s*"\*"\s*:', txt, re.MULTILINE):
			ERRORS.append('hooks.py contains a global doc_events["*"] (forbidden)')
	# Resolve referenced methods of the form coreerp.x.y.func
	# Exclude asset bundle strings (coreerp.bundle.css / .js).
	refs = set(re.findall(r"coreerp(?:\.[a-z0-9_]+)+\.[a-z0-9_]+", txt))
	refs = {r for r in refs if not r.endswith((".css", ".js"))}
	for ref in sorted(refs):
		parts = ref.split(".")
		func = parts[-1]
		mod_path = os.path.join(os.path.dirname(ROOT), *parts[:-1]) + ".py"
		if not os.path.exists(mod_path):
			ERRORS.append(f"hooks ref module missing: {ref} (expected {mod_path})")
			continue
		src = open(mod_path, encoding="utf-8").read()
		if not re.search(rf"def\s+{re.escape(func)}\b", src):
			ERRORS.append(f"hooks ref function missing: {ref}")


def check_compiles():
	for pf in find(r"\.py$"):
		try:
			ast.parse(open(pf, encoding="utf-8").read())
		except SyntaxError as e:
			ERRORS.append(f"SyntaxError in {pf}: {e}")


if __name__ == "__main__":
	known = collect_doctypes()
	print(f"Discovered {len(known)} CoreERP doctypes.")
	check_compiles()
	check_no_erpnext()
	check_hooks()
	check_json_and_links(known)

	print("\n--- WARNINGS ---")
	for w in WARN:
		print("  WARN:", w)
	print("\n--- ERRORS ---")
	for e in ERRORS:
		print("  ERR :", e)
	print(f"\n{len(ERRORS)} errors, {len(WARN)} warnings.")
	sys.exit(1 if ERRORS else 0)
