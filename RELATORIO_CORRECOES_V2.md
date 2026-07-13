# Relatório de Investigação e Correções de Nutrientes - Fase 2

Este relatório detalha as ações tomadas para resolver os problemas críticos de extração de Cálcio Máximo, baixa cobertura de Fibra e perda de registros de Fósforo.

## 1. Diagnóstico e Soluções

### 1.1. Cálcio Máximo (`calcium_max_mgkg`)
- **Problema**: O parser estava configurado para retornar apenas o primeiro match de cada nutriente. Quando o texto continha "Cálcio (mín) ... Cálcio (máx)", o match de "Cálcio (mín)" (muitas vezes via alias genérico "Cálcio") consumia a posição e impedia a extração do máximo.
- **Solução**: 
    - O parser foi atualizado (v1.3.14) para permitir múltiplos matches do mesmo nutriente em posições diferentes.
    - O `executar_pipeline.py` foi ajustado para processar todos os matches retornados.
    - Os aliases de cálcio foram refinados para lidar com variações de pontuação (ex: `máx.` vs `máx`).

### 1.2. Fibra (`fiber_gkg`)
- **Problema**: Cobertura baixa devido a aliases limitados e falhas no separador de regex quando o rótulo continha caracteres especiais.
- **Solução**:
    - Expansão dos aliases para incluir termos como "extrato fibroso" e "material fibroso".
    - Ajuste no `SEPARATOR` do regex (v1.3.14) para ser mais permissivo e não guloso, garantindo que o valor seja capturado mesmo após parênteses ou traços.

### 1.3. Fósforo (`phosphorus_mgkg`)
- **Problema**: Perda de registros identificada (88 registros). A investigação apontou que a auditoria biológica de Razão Ca:P era muito rígida (limite 3.0), invalidando produtos com alto cálcio.
- **Solução**:
    - A razão Ca:P na auditoria biológica foi relaxada de 3.0 para **4.5** (v1.3.4). Isso preserva produtos legítimos (como petiscos ou rações com minerais adicionados) enquanto ainda protege contra erros grosseiros de escala.

## 2. Resultados dos Testes

Os testes de reprodução confirmaram a eficácia das mudanças:
- **Cálcio Mín e Máx**: Agora extraídos simultaneamente no mesmo produto.
- **Fibra**: Captura correta em diversos formatos de unidade (% e g/kg).
- **Fósforo**: Preservado mesmo em razões Ca:P elevadas (ex: 4.0).

## 3. Próximos Passos
- Monitorar a execução do pipeline completo para validar se a cobertura de fósforo retornou aos níveis esperados (> 90%).
- Verificar se a discrepância entre cálcio mínimo e máximo foi reduzida no catálogo final.
