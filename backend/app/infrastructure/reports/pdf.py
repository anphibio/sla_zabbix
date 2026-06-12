from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path


def _ensure_reportlab() -> None:
    try:
        import reportlab  # noqa: F401
        return
    except ModuleNotFoundError:
        home = Path.home()
        candidate = (
            home
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "python"
            / "lib"
        )
        versions = sorted(candidate.glob("python*/site-packages"))

        for site_packages in versions:
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.append(site_packages_str)


_ensure_reportlab()

from reportlab.lib import colors  # type: ignore  # noqa: E402
from reportlab.lib.pagesizes import A4  # type: ignore  # noqa: E402
from reportlab.pdfgen import canvas  # type: ignore  # noqa: E402


def build_executive_sla_pdf(payload: dict[str, object]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4
    margin_x = 48
    y = height - 52

    summary = payload["summary"]
    services = payload["services"]

    pdf.setTitle("Consolidacao Executiva de SLA")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin_x, y, "Consolidacao Executiva de SLA")
    y -= 26

    pdf.setFont("Helvetica", 10)
    source_label = payload.get("source_type") or "todos"
    pdf.drawString(margin_x, y, f"Periodo: {summary['period_start']} ate {summary['period_end']}")
    y -= 14
    pdf.drawString(margin_x, y, f"Fonte: {source_label}")
    y -= 22

    y = _draw_summary_block(pdf, margin_x, y, summary)
    y -= 24

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin_x, y, "Servicos")
    y -= 16

    headers = [
        ("Servico", 140),
        ("Origem", 70),
        ("Disp.", 55),
        ("Meta", 45),
        ("Status", 55),
        ("Down", 45),
        ("Base", 50),
    ]

    y = _draw_services_table(pdf, margin_x, y, headers, services, height)

    pdf.save()
    return buffer.getvalue()


def _draw_summary_block(pdf, x: int, y: float, summary: dict[str, object]) -> float:
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x, y, "Resumo")
    y -= 16
    pdf.setFont("Helvetica", 10)

    lines = [
        f"Quantidade de servicos: {summary['services_count']}",
        f"Servicos conformes: {summary['compliant_services_count']}",
        f"Servicos fora da meta: {summary['non_compliant_services_count']}",
        f"Disponibilidade ponderada: {summary['weighted_availability_percent']}",
        f"Disponibilidade media: {summary['average_availability_percent']}",
        f"Melhor disponibilidade: {summary['best_availability_percent']}",
        f"Pior disponibilidade: {summary['worst_availability_percent']}",
    ]

    for line in lines:
        pdf.drawString(x, y, line)
        y -= 14

    return y


def _draw_services_table(pdf, x: int, y: float, headers, services, page_height: float) -> float:
    row_height = 18
    bottom_margin = 48

    def draw_header(current_y: float) -> float:
        pdf.setFillColor(colors.HexColor("#D9E3F0"))
        pdf.rect(x, current_y - row_height + 4, sum(width for _, width in headers), row_height, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 9)
        cursor_x = x + 4
        for label, width in headers:
            pdf.drawString(cursor_x, current_y - 9, label)
            cursor_x += width
        return current_y - row_height

    y = draw_header(y)
    pdf.setFont("Helvetica", 8.5)

    for index, item in enumerate(services):
        if y < bottom_margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 8.5)
            y = page_height - 52
            y = draw_header(y)

        if index % 2 == 0:
            pdf.setFillColor(colors.HexColor("#F7F9FC"))
            pdf.rect(x, y - row_height + 4, sum(width for _, width in headers), row_height, fill=1, stroke=0)
            pdf.setFillColor(colors.black)

        values = [
            item["service_key"],
            item["source_type"],
            str(item["availability_percent"]),
            str(item["target_percentage"]),
            "OK" if item["meets_target"] else "Fora",
            str(item["downtime_minutes"]),
            str(item["total_minutes"]),
        ]
        cursor_x = x + 4
        for (label, width), value in zip(headers, values):
            text = str(value)
            if len(text) > 22:
                text = text[:19] + "..."
            pdf.drawString(cursor_x, y - 9, text)
            cursor_x += width
        y -= row_height

    return y
