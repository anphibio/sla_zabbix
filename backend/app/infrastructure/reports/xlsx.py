from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def build_executive_sla_xlsx(payload: dict[str, object]) -> bytes:
    workbook_buffer = BytesIO()

    with ZipFile(workbook_buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        archive.writestr("xl/styles.xml", _styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _summary_sheet_xml(payload))
        archive.writestr("xl/worksheets/sheet2.xml", _services_sheet_xml(payload))

    return workbook_buffer.getvalue()


def _content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""


def _root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""


def _workbook_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Resumo" sheetId="1" r:id="rId1"/>
    <sheet name="Servicos" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>"""


def _workbook_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf/></cellStyleXfs>
  <cellXfs count="1"><xf xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _summary_sheet_xml(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    rows = [
        ["Indicador", "Valor"],
        ["Periodo inicial", summary["period_start"]],
        ["Periodo final", summary["period_end"]],
        ["Fonte", payload.get("source_type") or "todos"],
        ["Quantidade de servicos", summary["services_count"]],
        ["Servicos conformes", summary["compliant_services_count"]],
        ["Servicos fora da meta", summary["non_compliant_services_count"]],
        ["Disponibilidade ponderada", summary["weighted_availability_percent"] or ""],
        ["Disponibilidade media", summary["average_availability_percent"] or ""],
        ["Melhor disponibilidade", summary["best_availability_percent"] or ""],
        ["Pior disponibilidade", summary["worst_availability_percent"] or ""],
    ]
    return _worksheet_xml(rows)


def _services_sheet_xml(payload: dict[str, object]) -> str:
    rows = [[
        "Servico",
        "Regra",
        "Origem",
        "Disponibilidade",
        "Meta",
        "Atingiu meta",
        "Downtime (min)",
        "Base elegivel (min)",
    ]]

    for item in payload["services"]:
        rows.append([
            item["service_key"],
            item["rule_name"],
            item["source_type"],
            item["availability_percent"],
            item["target_percentage"],
            "sim" if item["meets_target"] else "nao",
            item["downtime_minutes"],
            item["total_minutes"],
        ])

    return _worksheet_xml(rows)


def _worksheet_xml(rows: list[list[object]]) -> str:
    sheet_rows = []

    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            cell_ref = f"{_column_name(column_index)}{row_index}"
            cells.append(_cell_xml(cell_ref, value))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )


def _cell_xml(cell_ref: str, value: object) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{cell_ref}"><v>{value}</v></c>'

    text = escape(str(value))
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _column_name(index: int) -> str:
    result = ""
    current = index

    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result

    return result
