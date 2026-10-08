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
    'test_access_rule[website POST /api/codebook/upload -> deny (other websites get nothing)]': 'F2',
    'test_access_rule[rebinding POST /api/codebook/upload -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/codebook/meta -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/codebook/ -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[website POST /api/studies/upload -> deny (other websites get nothing)]': 'F2',
    'test_access_rule[rebinding POST /api/studies/upload -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/studies/ -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding DELETE /api/studies/ACE_Test -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/initialise/run -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/initialise/status -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[website POST /api/initialise/clear-workspace -> deny (other websites get nothing)]': 'F2',
    'test_access_rule[rebinding POST /api/initialise/clear-workspace -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test/variable/age -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding PUT /api/mappings/ACE_Test/variable/age -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding PUT /api/mappings/ACE_Test/variable/age/reopen -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/mappings/ACE_Test/audit -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/mappings/preview-transformation -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/mappings/validate-expression -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/download/ACE_Test/mapping-csv -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/download/transformed-data -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/download/audit-log -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/ai-config/providers -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/ai-config/test -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/ai-config/models -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/issue-url -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/afpo/lookup -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/afpo/gaps/submitted -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding POST /api/afpo/gaps/unsubmitted -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/check-github -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_access_rule[rebinding GET /api/afpo/ontology-status -> deny (DNS-rebinding sites get nothing)]': 'F3',
    'test_website_cannot_wipe_the_workspace': 'F2',
    'test_rebinding_site_cannot_read_studies': 'F3',
    'test_run_backend_listens_on_localhost_by_default': 'F1',
    'test_compose_publishes_on_localhost_by_default[docker-compose.yml]': 'F1',
    'test_compose_publishes_on_localhost_by_default[docker-compose.hub.yml]': 'F1',
}


def pytest_collection_modifyitems(items):
    for item in items:
        finding = KNOWN_FAILURES.get(item.name)
        if finding:
            item.add_marker(pytest.mark.xfail(strict=True, reason=REASONS[finding]))
