
import pandas as pd
from app.parsers.html_parser import extract_guarantee_section
from app.semantic.engine import SemanticEngine

def test_html_guarantee_detection():
    # Caso: Layout com 'Componentes Analíticos' (comum em importadas)
    html = """
    <html>
        <body>
            <div>Descrição do produto</div>
            <h3>Componentes Analíticos</h3>
            <p>Proteína Bruta: 25%</p>
            <p>Gordura: 15%</p>
            <h3>Ficha Técnica</h3>
        </body>
    </html>
    """
    section = extract_guarantee_section(html)
    assert section is not None
    assert "Proteína Bruta: 25%" in section
    print("  - Detecção de 'Componentes Analíticos': OK")

def test_lifestage_name_fallback():
    engine = SemanticEngine()
    data = [
        {
            "product_id": "1",
            "product_name": "Ração Úmida Pet Delícia Cães Filhotes Papinha de Frango",
            "life_stage": "nan" # Simula erro de extração da ficha técnica
        }
    ]
    df = pd.DataFrame(data)
    enriched = engine.enrich_dataframe(df)
    assert enriched.loc[0, "life_stage"] == "Filhote"
    print("  - Fallback de Life Stage via nome (Filhotes): OK")

def test_tier_mapping_consistency():
    engine = SemanticEngine()
    data = [
        {
            "product_id": "2",
            "product_name": "Ração Teste",
            "product_type": "Super Premium Natural",
            "product_line": "Biofresh"
        },
        {
            "product_id": "3",
            "product_name": "Ração Teste 2",
            "product_type": "Ração Seca",
            "product_line": "Premium Especial"
        }
    ]
    df = pd.DataFrame(data)
    enriched = engine.enrich_dataframe(df)
    assert enriched.loc[0, "product_tier"] == "Super Premium"
    assert enriched.loc[1, "product_tier"] == "Premium Especial"
    print("  - Mapeamento dinâmico de Tier (Super Premium / Premium Especial): OK")

if __name__ == "__main__":
    print("Iniciando testes de extração v1.5.5...")
    test_html_guarantee_detection()
    test_lifestage_name_fallback()
    test_tier_mapping_consistency()
    print("\nTodos os testes de extração v1.5.5 passaram!")
