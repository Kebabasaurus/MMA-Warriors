"""End-to-end hidden-Tk acceptance audit for the MMA Warriors database editor.

This intentionally uses the editor's widgets and public Apply commands rather
than inspecting JSON in isolation. It is safe to run: no database is saved.
"""

from copy import deepcopy
import tkinter as tk

import database_editor as editor_module
from database_editor import UNSET_CHOICE_LABEL, UniverseDatabaseEditor, compact_json, json_value


def fail(title, message):
    raise AssertionError(f"{title}: {message}")


def exact_widget_value(app, kind, field, value):
    """Assert the current editor control faithfully represents one stored value."""
    app.field_choice_changed(kind)
    choices = app.value_choices_for(kind, field)
    if kind == "fighter":
        choice, numeric, text = app.fighter_value_choice, app.fighter_value_number, app.fighter_value_text
    else:
        choice, numeric, text = app.company_value_choice, app.company_value_number, app.company_value_text
    if choices:
        shown = choice.get()
        expected = UNSET_CHOICE_LABEL if value in (None, "") else str(value).lower() if isinstance(value, bool) else str(value)
        if shown != expected:
            fail("dropdown value", f"{kind}.{field}: expected {expected!r}, found {shown!r}")
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        shown = json_value(numeric.get())
        if shown != value:
            fail("numeric value", f"{kind}.{field}: expected {value!r}, found {shown!r}")
        return
    shown = json_value(text.get("1.0", "end"))
    if shown != value:
        fail("text value", f"{kind}.{field}: expected {value!r}, found {shown!r}")


def audit_all_visible_values(app, kind):
    rows = app.fighter_records() if kind == "fighter" else app.company_records() + app.regional_company_records()
    checked = 0
    for index, record in enumerate(rows):
        if kind == "fighter":
            app.fighter_selection = index
            app.refresh_fighter_editor()
            field_var = app.fighter_field_var
        else:
            app.company_selection = str(index) if index < len(app.company_records()) else f"regional:{index - len(app.company_records())}"
            app.refresh_company_editor()
            field_var = app.company_field_var
        for field, value in record.items():
            field_var.set(field)
            exact_widget_value(app, kind, field, value)
            checked += 1
    return checked


def audit_apply_paths(app, kind):
    rows = app.fighter_records() if kind == "fighter" else app.company_records() + app.regional_company_records()
    seen = set()
    checked = 0
    for index, record in enumerate(rows):
        for field, value in record.items():
            if field in seen:
                continue
            seen.add(field)
            if kind == "fighter":
                app.fighter_selection = index
                app.refresh_fighter_editor()
                app.fighter_field_var.set(field)
            else:
                app.company_selection = str(index) if index < len(app.company_records()) else f"regional:{index - len(app.company_records())}"
                app.refresh_company_editor()
                app.company_field_var.set(field)
            before = deepcopy(value)
            exact_widget_value(app, kind, field, value)
            app.apply_field(kind)
            if record.get(field) != before:
                fail("apply path", f"{kind}.{field} changed {before!r} to {record.get(field)!r}")
            checked += 1
    return checked


def audit_rating_controls(app):
    index = next(index for index, row in enumerate(app.fighter_records()) if row.get("name") == "Paddy Pimblett")
    app.fighter_selection = index
    app.refresh_fighter_editor()
    record = app.selected_fighter()
    for field, _label in app.CORE_RATING_FIELDS:
        value = record[field]
        app.fighter_core_rating_scales[field].set(value)
        if int(app.fighter_core_rating_vars[field].get()) != value:
            fail("core slider", f"{field}: slider did not select {value}")
    app.apply_core_ratings()
    for field, _label in app.CORE_RATING_FIELDS:
        if record[field] != int(app.fighter_core_rating_vars[field].get()):
            fail("core apply", f"{field} did not persist")
    for group, skills in editor_module.DETAILED_SKILL_GROUPS.items():
        for skill in skills:
            value = record["signature_skills"][skill]
            scale = app.fighter_skill_scales[skill]
            scale.set(value)
            if int(app.fighter_skill_vars[skill].get()) != value:
                fail("detailed slider", f"{group}.{skill}: slider did not select {value}")
    if not app.apply_skill_sheet():
        fail("detailed apply", "full skill sheet did not apply")
    for group, skills in editor_module.DETAILED_SKILL_GROUPS.items():
        for skill in skills:
            value = int(app.fighter_skill_vars[skill].get())
            if record["signature_skills"][skill] != value:
                fail("detailed apply", f"{group}.{skill} did not persist")
    app.sync_core_ratings_from_skill_sheet()
    current = int(record["profile_rating"])
    suggested = app.suggested_overall_for_record(record, skill_overrides=record["signature_skills"])
    if current < 1 or suggested < 1:
        fail("suggested overall", "skill sheet did not produce a valid OVR")
    return len(app.CORE_RATING_FIELDS), sum(len(skills) for skills in editor_module.DETAILED_SKILL_GROUPS.values())


def audit_authored_prime_windows(app):
    checked = 0
    for record in app.fighter_records():
        start = record.get("prime_start")
        end = record.get("prime_end")
        archetype = record.get("career_archetype")
        if not isinstance(start, int) or not isinstance(end, int) or not 18 <= start < end <= 40:
            fail("prime window", f"{record.get('name')}: invalid {start!r}-{end!r}")
        if archetype not in ("Early Maturation", "Balanced Development", "Late Maturation", "Durable Career"):
            fail("career archetype", f"{record.get('name')}: {archetype!r}")
        checked += 1
    return checked


def main():
    # The audit only feeds valid values back through the UI; suppress message
    # boxes so it can run unattended in CI or a release check.
    editor_module.messagebox.showerror = lambda *_args, **_kwargs: None
    editor_module.messagebox.showinfo = lambda *_args, **_kwargs: None
    root = tk.Tk()
    root.withdraw()
    try:
        app = UniverseDatabaseEditor(root)
        fighter_values = audit_all_visible_values(app, "fighter")
        company_values = audit_all_visible_values(app, "company")
        fighter_fields = audit_apply_paths(app, "fighter")
        company_fields = audit_apply_paths(app, "company")
        core_fields, detailed_skills = audit_rating_controls(app)
        prime_windows = audit_authored_prime_windows(app)
        print(
            "DATABASE_EDITOR_UI_AUDIT_OK "
            f"fighter_values={fighter_values} company_values={company_values} "
            f"fighter_fields={fighter_fields} company_fields={company_fields} "
            f"core_fields={core_fields} detailed_skills={detailed_skills} prime_windows={prime_windows}"
        )
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
