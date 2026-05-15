from pathlib import Path

from ppd.logic.requirement_delta_review import build_requirement_delta_review_queue, load_json_snapshot


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'requirement_delta_review' / 'source_hash_delta_case.json'


def test_fixture_requirement_delta_review_queue_cases():
    fixture = load_json_snapshot(FIXTURE_PATH)

    for case in fixture['cases']:
        queue = build_requirement_delta_review_queue(
            case['previous_snapshot'],
            case['current_snapshot'],
        )
        assert queue == case['expected_queue'], case['name']


def test_changed_deltas_always_report_review_and_readiness_status():
    fixture = load_json_snapshot(FIXTURE_PATH)
    case = fixture['cases'][0]
    queue = build_requirement_delta_review_queue(case['previous_snapshot'], case['current_snapshot'])

    assert queue['delta_count'] == 3
    for delta in queue['deltas']:
        assert delta['affected_process_ids']
        assert delta['guardrail_bundle_ids']
        assert delta['human_review_status'] == 'needs_review'
        assert delta['blocked_readiness_status'] == 'blocked_pending_human_review'
