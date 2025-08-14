import re

# Lista med rubriker vi vill bevara
SECTION_HEADERS = [
    "Executive Summary",
    "Key Insights",
    "Financial Highlights",
    "Recommendations"
]

def format_report_md(raw_text: str) -> str:
    """
    Formaterar rå text till ren Markdown med korrekta rubriker och bullets.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()
    text = re.sub(r"\.\.\. \[truncated for length\]", "", text)

    # Normalisera bullets till '- '
    text = re.sub(r"^[\s]*[•\*\-]\s*", "- ", text, flags=re.MULTILINE)

    # Lägg till två radbrytningar efter rubriker
    for header in SECTION_HEADERS:
        pattern = rf"(?m)^(#+\s*{re.escape(header)})\s*$"
        text = re.sub(pattern, r"\1\n\n", text)

    # Säkerställ att slutmarkörer är på egen rad
    text = re.sub(r"---\s*End of [^\n]+---", lambda m: "\n" + m.group(0) + "\n", text)

    # Ta bort överflödiga mellanslag på varje rad
    text = "\n".join(line.rstrip() for line in text.splitlines())

    # Max en tom rad mellan textblock
    formatted_lines = []
    prev_blank = False
    for line in text.splitlines():
        if line.strip() == "":
            if not prev_blank:
                formatted_lines.append("")
            prev_blank = True
        else:
            formatted_lines.append(line)
            prev_blank = False

    return "\n".join(formatted_lines)

def format_final_report(company_name: str, raw_agent_outputs: list, sources: list) -> str:
    """
    Kombinerar flera agent-outputs till en komplett Markdown-rapport.
    """
    if not raw_agent_outputs:
        return f"# Company Analysis Report for {company_name}\n\nNo analysis data available."

    combined_text = "\n\n".join([str(output) for output in raw_agent_outputs if output])
    if not combined_text.strip():
        return f"# Company Analysis Report for {company_name}\n\nNo analysis data available."

    formatted_text = format_report_md(combined_text)

    report = f"# Company Analysis Report for {company_name}\n\n{formatted_text}"

    if sources:
        report += "\n\n## Sources\n"
        for source in sources:
            if source.strip():
                report += f"- {source.strip()}\n"

    return report


def extract_sections(raw_text: str) -> dict:
    """
    Extraherar rapportens huvudsektioner baserat på slutmarkörer.
    Returnerar en dict med sektionens namn som nyckel och text som värde.
    """
    sections = {}
    pattern = re.compile(r"(.*?)(--- End of [^\n]+---)", re.DOTALL)
    matches = pattern.findall(raw_text)
    for match in matches:
        content, marker = match
        key = marker.replace("--- End of ", "").replace("---", "").strip()
        sections[key] = content.strip()
    return sections


