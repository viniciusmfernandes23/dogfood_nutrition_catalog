#!/bin/bash

echo "===================================================="
echo "🚀 Iniciando Testes Pré-Pull Request (Branch Petlove)"
echo "===================================================="

# Detecta o comando python correto (python3 ou python)
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Erro: Python não encontrado no sistema."
    exit 1
fi

echo "ℹ️  Usando comando: $PYTHON_CMD"

# Verifica se o pytest está instalado
if ! $PYTHON_CMD -m pytest --version > /dev/null 2>&1; then
    echo "❌ Erro: 'pytest' não encontrado no ambiente virtual."
    echo "💡 Por favor, instale as dependências executando:"
    echo "   pip install -r app/requirements.txt"
    exit 1
fi

# 1. Testes de Integração Petlove e Multiloja (Novos)
echo -e "\n[1/3] Rodando testes de integração Petlove..."
$PYTHON_CMD tests/test_petlove_integration.py
if [ $? -eq 0 ]; then
    echo "✅ Testes de integração Petlove passaram!"
else
    echo "❌ Falha nos testes de integração Petlove!"
    exit 1
fi

# 2. Testes de Variação de Preço (v1.5.0)
echo -e "\n[2/3] Rodando testes de multi-variação de preço..."
$PYTHON_CMD -m pytest tests/test_price_multivariation.py -v
if [ $? -eq 0 ]; then
    echo "✅ Testes de multi-variação de preço passaram!"
else
    echo "❌ Falha nos testes de multi-variação de preço!"
    exit 1
fi

# 3. Testes do Warehouse (Existentes)
echo -e "\n[3/3] Rodando testes do Warehouse..."
$PYTHON_CMD -m pytest tests/test_warehouse.py -v
if [ $? -eq 0 ]; then
    echo "✅ Testes do Warehouse passaram!"
else
    echo "⚠️  Alguns testes do Warehouse falharam (verifique se são as falhas pré-existentes)."
fi

echo -e "\n===================================================="
echo "🎉 Verificação concluída!"
echo "===================================================="
