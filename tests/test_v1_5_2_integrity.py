
import pandas as pd
from app.semantic.engine import SemanticEngine
from app.warehouse.dim_product import ProductDimensionBuilder

def test_tier_and_lifestage_logic():
    engine = SemanticEngine()
    
    # Caso 1: Super Premium na Ficha Técnica (product_type)
    # Caso 2: Life Stage 'Filhote' no nome
    # Caso 3: Premium Especial na Ficha Técnica (product_line)
    # Caso 4: ID Vazio (deve ser ignorado)
    
    data = [
        {
            "product_id": 1,
            "product_name": "Ração Comum Adulto",
            "product_type": "Super Premium Natural",
            "life_stage": None
        },
        {
            "product_id": 2,
            "product_name": "Ração Úmida Pet Delícia Cães Filhotes Papinha",
            "product_type": "Premium",
            "life_stage": ""
        },
        {
            "product_id": 3,
            "product_name": "Ração Intermediária",
            "product_type": "Ração Seca",
            "product_line": "Premium Especial",
            "life_stage": None
        },
        {
            "product_id": "", # ID Vazio
            "product_name": "Produto Inválido",
            "product_type": "Standard",
            "life_stage": "Adulto"
        }
    ]
    df = pd.DataFrame(data)
    
    # 1. Testar Enriquecimento Semântico
    enriched_df = engine.enrich_dataframe(df)
    
    # Prod 1 deve ser Super Premium
    assert enriched_df.loc[0, "product_tier"] == "Super Premium"
    assert enriched_df.loc[0, "life_stage"] == "Adulto"
    
    # Prod 2 deve ser Filhote (via nome) e Premium (via ficha técnica)
    assert enriched_df.loc[1, "life_stage"] == "Filhote"
    assert enriched_df.loc[1, "product_tier"] == "Premium"
    
    # Prod 3 deve ser Premium Especial (via product_line)
    assert enriched_df.loc[2, "product_tier"] == "Premium Especial"
    
    # 2. Testar Builder (Sanitização de IDs)
    builder = ProductDimensionBuilder()
    dim_df = builder.build(enriched_df)
    
    # O produto com ID vazio deve ter sido removido
    assert len(dim_df) == 3
    assert "" not in dim_df["product_id"].values
    assert "gender" not in dim_df.columns

if __name__ == "__main__":
    print("Iniciando testes de integridade v1.5.2...")
    test_tier_and_lifestage_logic()
    print("  - Lógica de Tier (Super Premium): OK")
    print("  - Lógica de Life Stage (Fallback Nome): OK")
    print("  - Sanitização de IDs e Remoção de Gender: OK")
    print("\nTodos os testes de integridade v1.5.2 passaram!")
