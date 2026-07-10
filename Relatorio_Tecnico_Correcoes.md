# Relatório Técnico: Evolução e Correções do Pipeline Dog Food Nutrition Catalog

**Autor:** Manus AI
**Data:** 10 de Julho de 2026
**Versão do Pipeline:** v1.4.0

## 1. Introdução

Este documento detalha as correções e melhorias implementadas no pipeline `Dog Food Nutrition Catalog` desde a versão `v1.2.0` até a `v1.4.0`. O objetivo principal foi resolver problemas críticos de integridade de dados, como valores nutricionais biologicamente impossíveis, inconsistências de data e artefatos de ponto flutuante, além de introduzir um robusto sistema de auditoria de coerência nutricional.

## 2. Histórico de Correções e Justificativas

### 2.1. v1.2.0 - Eliminação de Dados Antigos e Valores Impossíveis
- **Problema:** Persistência de dados antigos (`1.7e16` para sódio) e energia inflada (`35000` kcal/kg).
- **Causa:** Exportação incremental (`append`) que preservava arquivos e falha na deduplicação de preços.
- **Solução:** Desativação da escala legada, limpeza total de nutrientes no modo `full` e implementação de auto-correção recursiva no `Resolver`.

### 2.2. v1.2.1 - Sincronização de Timezone e Limpeza de Cache
- **Problema:** Inconsistência na coluna `collected_at` entre as tabelas e falha no carregamento de novos módulos Python.
- **Causa:** Uso de `UTC` em ambientes brasileiros e cache de arquivos `.pyc`.
- **Solução:** Padronização para **Horário Local**, centralização do timestamp no `WarehousePipeline` e implementação da "Bomba de Limpeza de Cache" no início da execução.

### 2.3. v1.2.2 - Trava de Imutabilidade e Tolerância Zero
- **Problema:** Re-normalização em cascata transformando valores corretos em astronômicos.
- **Causa:** O `Resolver` aplicava conversões repetidamente se a unidade original estivesse presente no DataFrame.
- **Solução:** Implementação de trava de plausibilidade (ignora unidade se o valor já for válido) e redução do limite de anulação para `100.000`.

### 2.4. v1.2.3 - Trava de Sanidade Final no Exporter
- **Problema:** Artefatos corrompidos escapavam para o CSV final.
- **Solução:** Implementação da **Barreira de Sanidade Final** no `WarehouseExporter`, validando limites físicos no milissegundo antes da gravação do arquivo.

### 2.5. v1.2.4 - Eliminação de Artefatos de Ponto Flutuante
- **Problema:** Valores como `1700.0000000000002` causavam exibição confusa no Excel.
- **Causa:** Imprecisão binária do padrão IEEE 754 em operações com `float`.
- **Solução:** Arredondamento global para **2 casas decimais** no `Resolver` e no `Exporter`.

### 2.6. v1.3.1 - Modo de Segurança Biológica e Âncora de Umidade
- **Problema:** Heurísticas de multiplicação agressivas causaram inflação de energia em rações úmidas.
- **Solução:** Desativação de multiplicações cegas e introdução da **Âncora de Umidade** (Umidade > 70% -> Max Energia 1500 kcal/kg).

### 2.7. v1.3.3 - Correção de Persistência no Modo Price
- **Problema:** O modo `--mode price` sobrescrevia o arquivo de nutrientes com conteúdo vazio.
- **Solução:** Adicionada verificação `if dataframe.empty` para proteger dados históricos durante atualizações de preço.

### 2.8. v1.4.0 - Arquitetura Consolidada e Auditoria Cruzada
- **Padronização de Unidades:** Definição oficial de `g/kg`, `mg/kg` e `kcal/kg` no novo `SCHEMA.md`.
- **Auditoria Cinzas vs Minerais:** Nova regra que valida se a soma dos minerais é compatível com o teor de cinzas totais.
- **Documentação de Esquema:** Criação do `SCHEMA.md` para governança de dados.
- **Sincronização Total:** Eliminação definitiva de resquícios de Timezone UTC, operando 100% em horário local.

## 3. Conclusão

O pipeline evoluiu de um simples crawler para um sistema de auditoria nutricional profissional. A filosofia de **"Integridade Biológica sobre Correção Heurística"** garante que o catálogo final seja uma fonte confiável para análises de BI e nutrição animal.
