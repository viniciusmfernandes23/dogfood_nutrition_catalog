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

    # v1.5.2: Aliases para seção de garantia
    guarantee_markers = [
        "níveis de garantia",
        "niveis de garantia",
        "garantia",
        "análise garantida",
        "analise garantida",
        "composição",
        "composicao",
    ]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(marker in line_lower for marker in guarantee_markers):
            # Se for composição, queremos garantir que não é apenas a lista de ingredientes
            # mas sim que contém níveis. Heurística: se a linha ou as próximas contêm '%' ou 'g/kg'
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