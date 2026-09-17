from __future__ import annotations

import pandas as pd


class ProductReviewFactBuilder:
    """Constrói o fato de comentários de avaliações de produtos."""

    COLUMNS = ("product_id", "comment")

    def build(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        if dataframe.empty:
            return pd.DataFrame(columns=self.COLUMNS)

        records: list[dict[str, object]] = []
        for row in dataframe.to_dict(orient="records"):
            product_id = row.get("product_id")
            comments = row.get("product_comments") or []
            if product_id is None or not isinstance(comments, list):
                continue

            seen_comments: set[str] = set()
            for value in comments:
                if not isinstance(value, str):
                    continue
                comment = " ".join(value.split())
                if comment and comment not in seen_comments:
                    records.append({"product_id": product_id, "comment": comment})
                    seen_comments.add(comment)

        if not records:
            return pd.DataFrame(columns=self.COLUMNS)

        return (
            pd.DataFrame(records, columns=self.COLUMNS)
            .drop_duplicates(subset=list(self.COLUMNS), keep="last")
            .sort_values(["product_id", "comment"], kind="stable")
            .reset_index(drop=True)
        )
