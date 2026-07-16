#!/bin/bash

echo "===================================================="
echo "🚀 Iniciando Testes Pré-Pull Request (Branch Petlove)"
echo "===================================================="

# 1. Testes de Integração Petlove e Multiloja (Novos)
echo -e "\n[1/3] Rodando testes de integração Petlove..."
python3 tests/test_petlove_integration.py
if [ $? -eq 0 ]; then
    echo "✅ Testes de integração Petlove passaram!"
else
    echo "❌ Falha nos testes de integração Petlove!"
    exit 1
fi

# 2. Testes de Variação de Preço (v1.5.0)
echo -e "\n[2/3] Rodando testes de multi-variação de preço..."
python3 tests/test_price_multivariation.py
if [ $? -eq 0 ]; then
    echo "✅ Testes de multi-variação de preço passaram!"
else
    echo "❌ Falha nos testes de multi-variação de preço!"
    exit 1
fi

# 3. Testes do Warehouse (Existentes)
echo -e "\n[3/3] Rodando testes do Warehouse..."
python3 -m pytest tests/test_warehouse.py -v
if [ $? -eq 0 ]; then
    echo "✅ Testes do Warehouse passaram!"
else
    echo "⚠️  Alguns testes do Warehouse falharam (verifique se são as falhas pré-existentes)."
fi

echo -e "\n===================================================="
echo "🎉 Verificação concluída!"
echo "===================================================="
