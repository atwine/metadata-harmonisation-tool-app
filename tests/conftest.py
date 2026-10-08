"""Known access failures, tracked until each fix lands (see ACCESS-AUDIT.md).

Each entry is marked xfail(strict=True): when a fix makes the test pass, the
run fails until the entry is deleted from KNOWN_FAILURES, so the list shrinks
with every fix and an empty dictionary means every access test is green.
"""

import pytest

REASONS = {
    "F1": "F1: API published beyond this computer (ACCESS-AUDIT.md)",
    "F2": "F2: no Origin check on state-changing requests (ACCESS-AUDIT.md)",
    "F3": "F3: no Host check, DNS rebinding possible (ACCESS-AUDIT.md)",
}

# test name (as pytest reports it, without the file) -> finding
KNOWN_FAILURES = {
}


def pytest_collection_modifyitems(items):
    for item in items:
        finding = KNOWN_FAILURES.get(item.name)
        if finding:
            item.add_marker(pytest.mark.xfail(strict=True, reason=REASONS[finding]))
