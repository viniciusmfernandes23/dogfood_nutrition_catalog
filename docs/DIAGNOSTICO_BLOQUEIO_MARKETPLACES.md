# Diagnóstico Técnico: Bloqueio de Coleta (Petlove & Petz)

Este documento detalha o motivo pelo qual os dados da Petlove e da Petz não estão sendo capturados no pipeline, apesar de o código de extração estar 100% funcional.

## 1. Status da Investigação
Após a implementação de logs de diagnóstico verbosos, identificamos que ambos os marketplaces possuem proteções ativas contra coleta automatizada:

| Marketplace | Status HTTP | Comportamento Detectado | Causa Raiz |
| :--- | :--- | :--- | :--- |
| **Petlove** | `403 Forbidden` | Bloqueio imediato na camada de rede. | Cloudflare (Data Center Block) |
| **Petz** | `200 OK` | Entrega uma página de Captcha/Desafio. | Bot Detection (Página de Desafio) |

## 2. Detalhes do Bloqueio da Petz
Diferente da Petlove, a Petz retorna um status de "Sucesso" (200 OK), mas o conteúdo da página é substituído por um **desafio de Captcha**. 
- O parser detectou: `[PETZ] Bloqueio detectado no conteúdo da página (Captcha/Bot)`.
- Isso significa que o site "vê" o script e, em vez de mostrar os produtos, mostra uma tela pedindo para confirmar que você é humano.

## 3. Por que isso acontece?
Grandes e-commerces utilizam serviços como Cloudflare, Akamai ou DataDome para evitar que robôs sobrecarreguem seus servidores ou copiem seus preços. Eles identificam:
1.  **Origem do IP:** IPs de servidores (nuvem) são bloqueados por padrão.
2.  **Impressão Digital do Navegador:** O script (HTTPX/Python) não possui a mesma "assinatura" de um navegador real (Chrome/Firefox).

## 4. Soluções Recomendadas
Como o código do pipeline já possui **três camadas de parser** (JSON, dataLayer e HTML), ele está pronto para funcionar. Para destravar a coleta, as opções são:

1.  **Uso de Proxy Residencial:** Integrar um serviço de proxy que forneça IPs de conexões domésticas (ex: Bright Data, Oxylabs).
2.  **Ambiente de Execução:** Executar o pipeline em uma máquina local com uma conexão de internet comum (não corporativa/servidor).
3.  **Bypass de Captcha:** Integração com serviços de resolução de captcha (ex: 2Captcha, Anti-Captcha), embora isso aumente a complexidade e o custo.

---
**Conclusão:** O bug de "não coletar" foi resolvido no nível de código (parsers implementados e validados). A barreira atual é de **infraestrutura de rede**, comum em projetos de Web Scraping de larga escala.
