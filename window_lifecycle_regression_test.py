"""Static invariant checks for the shared runtime popup registry."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME_MODULES = ("admin.py", "awards.py", "events.py", "persistence.py", "views.py")


def test_runtime_popup_creators_use_registry():
    offenders = []
    for filename in RUNTIME_MODULES:
        source = (ROOT / filename).read_text(encoding="utf-8")
        if "tk.Toplevel(" in source:
            offenders.append(filename)
        assert "create_managed_window" in source, f"{filename} has no managed popup entry point"
    assert not offenders, f"Unmanaged runtime popup creators remain: {', '.join(offenders)}"


def test_registry_keys_include_callsite_and_entity_identity():
    source = (ROOT / "ui.py").read_text(encoding="utf-8")
    assert "caller.f_code.co_filename" in source
    assert "caller.f_lineno" in source
    assert "fighter_id" in source


def test_fighter_profile_focus_and_creation_use_the_same_key():
    source = (ROOT / "views.py").read_text(encoding="utf-8")
    start = source.index("    def open_fighter_profile_window")
    end = source.index("    def open_regional_identity_window", start)
    profile_source = source[start:end]
    assert "focus_managed_window(profile_key)" in profile_source
    assert "create_managed_window(profile_key)" in profile_source


if __name__ == "__main__":
    test_runtime_popup_creators_use_registry()
    test_registry_keys_include_callsite_and_entity_identity()
    test_fighter_profile_focus_and_creation_use_the_same_key()
    print("WINDOW LIFECYCLE REGRESSION TEST PASSED")
