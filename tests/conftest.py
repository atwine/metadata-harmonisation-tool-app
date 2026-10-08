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
    'test_access_rule[rebinding GET /api/codebook/meta -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/codebook/ -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/studies/ -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/initialise/status -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test/variable/age -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test/audit -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/download/ACE_Test/mapping-csv -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/download/audit-log -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/ai-config/providers -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/ai-config/models -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/issue-url -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/check-github -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/ontology-status -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_rebinding_site_cannot_read_studies': 'F3',
}


def pytest_collection_modifyitems(items):
    for item in items:
        finding = KNOWN_FAILURES.get(item.name)
        if finding:
            item.add_marker(pytest.mark.xfail(strict=True, reason=REASONS[finding]))
