from tradepilot.evaluation import evaluate_dataset


def test_evaluation_reports_expected_metrics() -> None:
    metrics = evaluate_dataset("../data/evaluation/inquiries.json")
    assert metrics["cases"] == 6
    assert metrics["requirement_accuracy"] == 1.0
    assert metrics["product_match_rate"] == 1.0
    assert metrics["quote_success_rate"] == 1.0
    assert metrics["failure_detection_rate"] == 1.0
    assert metrics["failure_reasons"] == {"quantity": 1, "product": 1, "inventory": 1}
