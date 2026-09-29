from tradepilot.models import Product
from tradepilot.rag.products import build_product_document, retrieve_product_documents
from tradepilot.seed import seed_products


def test_product_document_contains_rag_relevant_business_fields(session) -> None:
    seed_products(session)
    product = session.query(Product).first()
    document = build_product_document(product)
    assert document.metadata["sku"] == product.sku
    assert "MOQ" in document.text
    assert product.name in document.text


def test_retrieval_returns_relevant_products_ranked_first(session) -> None:
    seed_products(session)
    results = retrieve_product_documents(session, "hotel aluminum chair", limit=3)
    assert results
    assert results[0].metadata["sku"] == "NOVA-CHAIR-001"
