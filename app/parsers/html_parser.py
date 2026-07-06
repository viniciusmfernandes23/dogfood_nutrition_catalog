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

    for i, line in enumerate(lines):

        if "níveis de garantia" in line.lower():

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