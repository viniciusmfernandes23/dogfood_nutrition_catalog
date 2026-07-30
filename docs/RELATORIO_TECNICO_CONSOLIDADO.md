# Relatório Técnico Consolidado

**Projeto:** Dog Food Nutrition Catalog  
**Versão de referência:** v2.1.0  
**Data de atualização:** 30 de julho de 2026

---

## 1. Resumo executivo

O projeto implementa um fluxo automatizado para coleta, normalização, validação e exportação de dados nutricionais e comerciais de alimentos para cães. A proposta principal é transformar informações brutas de marketplaces em um conjunto estruturalmente confiável, com rastreabilidade e prontidão para análise em ferramentas de BI.

O estado atual do repositório é de uma solução consolidada em termos de arquitetura, regras de normalização e fluxo operacional, com foco em robustez e documentação técnica.

---

## 2. Escopo e objetivos

Os objetivos do projeto são:
- garantir integridade biológica e semântica dos dados nutricionais;
- padronizar unidades e escalas para um formato comum;
- preservar contexto de validação e correção para auditoria;
- produzir dados estruturados para análise estratégica e visualização.

---

## 3. Arquitetura atual

### 3.1. Camada de ingestão
Os módulos de ingestão estão concentrados em [app/collectors](app/collectors) e [app/services](app/services).

Principais componentes:
- [app/collectors/cobasi_api.py](app/collectors/cobasi_api.py): integração com a Cobasi.
- [app/collectors/petlove_crawler.py](app/collectors/petlove_crawler.py): coletor de referência para a Petlove.
- [app/collectors/petz_collector.py](app/collectors/petz_collector.py): coletor de referência para a Petz.
- [app/services/collector_factory.py](app/services/collector_factory.py): fábrica de instâncias de collectors.
- [app/services/collection_service.py](app/services/collection_service.py): coordenação da execução multi-marketplace.
- [app/services/pipeline_runner.py](app/services/pipeline_runner.py): execução do fluxo completo.

### 3.2. Camada de processamento e normalização
A camada de processamento está localizada em [app/normalization](app/normalization), [app/parsers](app/parsers) e [app/semantic](app/semantic).

Principais componentes:
- [app/normalization/engine.py](app/normalization/engine.py): motor principal de normalização.
- [app/normalization/resolver.py](app/normalization/resolver.py): resolução de unidades e escalas.
- [app/normalization/validator.py](app/normalization/validator.py): validação de plausibilidade.
- [app/parsers/nutrition_parser.py](app/parsers/nutrition_parser.py): parsing nutricional.
- [app/semantic/classifier.py](app/semantic/classifier.py): classificação semântica de produtos.

### 3.3. Camada de exportação e warehouse
A camada de saída é responsável por consolidar os dados e gerar artefatos para análise.

Principais componentes:
- [app/warehouse](app/warehouse): exportação para modelos e tabelas analíticas.
- [app/pipeline](app/pipeline): orquestração, métricas e relatórios.

---

## 4. Regras de negócio e validações

### 4.1. Normalização nutricional
O motor atual valida e padroniza valores nutricionais por meio de:
- conversão de unidades;
- aplicação de regras biológicas e de plausibilidade;
- auditoria cruzada entre nutrientes;
- preservação do valor original e do contexto de correção.

### 4.2. Validações críticas
As validações principais incluem:
- balanço de massa;
- razão cálcio/fósforo;
- limites biológicos para microminerais;
- flexibilização de regras para categorias específicas, como petiscos e suplementos.

---

## 5. Situação atual das fontes de coleta

### 5.1. Cobasi
- fonte com melhor integração e execução consistente no fluxo principal.

### 5.2. Petlove e Petz
- a coleta de preços foi analisada e testada, mas não está validada como fluxo operacional estável;
- os bloqueios observados são de natureza externa ao projeto e impactam a viabilidade da extração em tempo real.

### 5.3. Implicação prática
- o pipeline permanece funcional para o fluxo geral de ingestão e exportação;
- a cobertura efetiva de preços para Petlove e Petz ainda depende de acesso autorizado, fontes alternativas ou estratégias específicas de bypass.

---

## 6. Validação recente

Os testes executados recentemente foram:
- `pytest -q tests/test_petlove_petz_collectors.py` → 2 passed
- `pytest -q tests/test_pipeline.py` → 12 passed

Esses resultados indicam estabilidade da base funcional do projeto, embora com limitações de cobertura para certas fontes externas.

---

## 7. Recomendações de manutenção

1. manter a documentação alinhada com o estado técnico real do projeto;
2. priorizar mudanças com evidência operacional e testes;
3. tratar bloqueios externos com transparência e sem sobreestimar a disponibilidade de dados;
4. manter a branch principal como referência da versão consolidada do repositório.

---

## 8. Conclusão

O projeto encontra-se em uma fase de consolidação técnica e documental, com uma arquitetura coerente, regras de normalização bem definidas e uma base operacional estável. O principal ponto de atenção hoje é a dependência de fontes externas para coleta de preços, e não a estrutura interna do pipeline.
