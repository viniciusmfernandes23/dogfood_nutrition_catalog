import pandas as pd
import numpy as np
import sys
import os

# Adiciona o diretório raiz ao path para importar a função
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executar_pipeline import format_currency

def test_format_currency():
    print("Iniciando testes da função format_currency...")
    
    test_cases = [
        (1500.5, "1500,50", "Float padrão"),
        (1500, "1500,00", "Integer"),
        ("1500.5", "1500,50", "String com ponto"),
        ("1500,5", "1500,50", "String com vírgula"),
        (None, None, "None value"),
        (np.nan, None, "Numpy NaN"),
        ("Texto Inválido", "Texto Inválido", "String não numérica"),
    ]
    
    success_count = 0
    for value, expected, description in test_cases:
        result = format_currency(value)
        if result == expected:
            print(f"✅ PASSED: {description} ({value} -> {result})")
            success_count += 1
        else:
            print(f"❌ FAILED: {description} ({value} -> {result}, esperado: {expected})")
            
    print(f"\nResultado: {success_count}/{len(test_cases)} testes passaram.")
    return success_count == len(test_cases)

if __name__ == "__main__":
    if test_format_currency():
        sys.exit(0)
    else:
        sys.exit(1)
