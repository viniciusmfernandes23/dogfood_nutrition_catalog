
from app.parsers.nutrition_parser import parse_nutrition, clean_numeric_value

def test_clean_numeric_value():
    # Padrão BR: Milhar com ponto, decimal com vírgula
    assert clean_numeric_value("3.700") == 3700.0
    assert clean_numeric_value("1.055,15") == 1055.15
    assert clean_numeric_value("10.530") == 10530.0
    
    # Padrão Simples
    assert clean_numeric_value("230") == 230.0
    assert clean_numeric_value("3,5") == 3.5
    assert clean_numeric_value("3.5") == 3.5

def test_aliases_capture():
    text = """
    Níveis de garantia
    Umidade (máx.) 100 g/kg (10%)
    Proteína bruta (mín.) 230 g/kg (23%)
    Extrato etéreo (mín.) 110 g/kg (11%)
    Matéria mineral (máx.) 80 g/kg (8%)
    Energia metabolizável (mín.) 3.700 kcal/kg
    """
    parsed = parse_nutrition(text)
    
    # Mapear resultados por nutriente
    results = {v['nutrient']: v['value'] for v in parsed.values()}
    
    assert results['protein'] == 230.0
    assert results['fat'] == 110.0  # Capturado via Extrato etéreo
    assert results['ash'] == 80.0   # Capturado via Matéria mineral
    assert results['metabolizable_energy'] == 3700.0

if __name__ == "__main__":
    print("Iniciando testes do parser v1.5.1...")
    test_clean_numeric_value()
    print("  - Limpeza de valores numéricos: OK")
    test_aliases_capture()
    print("  - Captura de aliases (Extrato Etéreo/Matéria Mineral): OK")
    print("\nTodos os testes do parser passaram!")
