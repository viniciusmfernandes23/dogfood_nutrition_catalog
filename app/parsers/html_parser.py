from bs4 import BeautifulSoup


def extract_guarantee_section(
    html: str | None,
) -> str | None:

    if html is None:
        return None

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    lines = text.splitlines()

    start = None

    # v1.5.5: Aliases exaustivos para seção de garantia
    guarantee_markers = [
        "níveis de garantia",
        "niveis de garantia",
        "garantia",
        "análise garantida",
        "analise garantida",
        "composição",
        "composicao",
        "constituintes analíticos",
        "componentes analíticos",
        "análise média",
        "informação nutricional",
        "informacao nutricional",
        "levels of guarantee",
        "guaranteed analysis",
    ]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # v1.5.5: Busca por match exato ou início de linha para evitar falsos positivos
        if any(marker in line_lower for marker in guarantee_markers):
            # Verificação adicional: a seção de garantia costuma ter valores numéricos próximos
            # Olhamos as próximas 10 linhas em busca de padrões de nutrientes (%, g/kg, mg/kg)
            found_values = False
            for j in range(i, min(i + 15, len(lines))):
                if any(u in lines[j].lower() for u in ["%", "g/kg", "mg/kg", "kcal", "ui/kg"]):
                    found_values = True
                    break
            
            if found_values:
                start = i
                break

    if start is None:

        return None

    end = len(lines)

    for i in range(start + 1, len(lines)):

        lower = lines[i].lower()

        if "ficha técnica" in lower:

            end = i

            break

    return "\n".join(lines[start:end])