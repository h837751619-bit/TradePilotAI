from tradepilot.evaluation import evaluate_dataset, evaluate_rag_dataset


def test_evaluation_reports_expected_metrics() -> None:
    metrics = evaluate_dataset("../data/evaluation/inquiries.json")
    assert metrics["cases"] == 6
    assert metrics["requirement_accuracy"] == 1.0
    assert metrics["product_match_rate"] == 1.0
    assert metrics["quote_success_rate"] == 1.0
    assert metrics["failure_detection_rate"] == 1.0
    assert metrics["failure_reasons"] == {"quantity": 1, "product": 1, "inventory": 1}


def test_rag_evaluation_reports_top_k_recall() -> None:
    metrics = evaluate_rag_dataset("../data/evaluation/rag_inquiries.json")
    assert metrics["cases"] == 16
    # The normalized product vocabulary makes the rule baseline useful for
    # common domain synonyms while semantic retrieval remains available for
    # more ambiguous or unseen phrasing.
    assert metrics["top1_recall"] == 0.875
    assert metrics["top3_recall"] == 0.9375
    assert 0 <= metrics["mrr"] <= 1
    assert isinstance(metrics["misses"], list)


def test_rag_evaluation_can_measure_semantic_recall() -> None:
    expected = {
        "Need 50 weatherproof seats for a seaside hotel project.": {"NOVA-CHAIR-001": 0.9},
        "We need 20 round dining surfaces for an Italian restaurant terrace.": {"NOVA-TABLE-001": 0.9},
        "Please quote 10 modular hospitality lounge units for a French resort.": {"NOVA-SOFA-001": 0.9},
        "请为中国海边酒店报价 50 把耐候户外座椅。": {"NOVA-CHAIR-001": 0.9},
        "Servono 20 tavoli rotondi per la terrazza di un ristorante italiano.": {"NOVA-TABLE-001": 0.9},
        "Necesitamos 10 módulos de sofá para la zona exterior de un hotel.": {"NOVA-SOFA-001": 0.9},
        "Looking for 30 stackable outdoor seats made from metal for a cafe.": {"NOVA-CHAIR-001": 0.9},
        "Quote 25 weather-resistant dining surfaces for a resort terrace.": {"NOVA-TABLE-001": 0.9},
        "A resort needs 40 pieces of commercial patio seating made from aluminium.": {"NOVA-CHAIR-001": 0.9},
        "请提供 30 把铝制户外椅，适用于餐厅露台。": {"NOVA-CHAIR-001": 0.9},
        "Cerchiamo 12 divani modulari per una lounge di un hotel.": {"NOVA-SOFA-001": 0.9},
        "Need 18 outdoor furniture dining sets for hotel balconies.": {"NOVA-SET-001": 0.9},
        "Please quote 15 commercial parasols for a restaurant terrace.": {"NOVA-UMBRELLA-001": 0.9},
        "We need 25 terrace tables for a hospitality project.": {"NOVA-TABLE-001": 0.9},
        "Looking for 8 modular outdoor couches for a resort.": {"NOVA-SOFA-001": 0.9},
        "酒店阳台需要 10 套户外家具组合。": {"NOVA-SET-001": 0.9},
    }
    metrics = evaluate_rag_dataset(
        "../data/evaluation/rag_inquiries.json", expected.__getitem__
    )
    assert metrics["mode"] == "semantic"
    assert metrics["top1_recall"] == 1.0
    assert metrics["top3_recall"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["misses"] == []
