import pandas as pd

from app.warehouse.fact_product_review import ProductReviewFactBuilder


def test_build_product_review_fact_uses_product_id_and_comment():
    dataframe = pd.DataFrame(
        {
            "product_id": [10, 10, 20],
            "product_comments": [
                [" Bom produto ", "Bom produto", "Entrega rápida"],
                ["Bom produto"],
                [],
            ],
        }
    )

    result = ProductReviewFactBuilder().build(dataframe)

    assert result.to_dict(orient="records") == [
        {"product_id": 10, "comment": "Bom produto"},
        {"product_id": 10, "comment": "Entrega rápida"},
    ]


def test_build_product_review_fact_empty_has_stable_columns():
    result = ProductReviewFactBuilder().build(pd.DataFrame())

    assert list(result.columns) == ["product_id", "comment"]
    assert result.empty