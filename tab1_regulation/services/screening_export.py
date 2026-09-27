"""제품별 최신 성분 스크리닝 결과를 XLSX 워크북으로 만듭니다."""
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


SHEET_NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
HEADERS=("제품명", "국가·권역", "분석일", "성분명(INCI)", "CAS 번호", "배합량(%)", "규제 유형", "판정 결과", "상세 조건")


def screening_rows(country,products,analyses_for):
    rows=[]
    for product in products:
        history=analyses_for(product["id"])
        if not history:
            continue
        latest=history[0]
        snapshot=latest["snapshot"]
        for ingredient in snapshot.get("results",[]):
            status=ingredient.get("result","")
            reason=ingredient.get("reason","")
            if status=="해당 없음":
                status="통과(Pass)"
                if reason=="등록 JSON에서 일치하는 적용 항목 없음":
                    reason="규제 항목 미해당 (사용 가능)"
            rows.append((
                snapshot.get("product",{}).get("name") or product["name"], country,
                latest["created_at"][:10], ingredient.get("inci_name") or ingredient.get("resolved_name") or "",
                ingredient.get("cas_no") or ingredient.get("resolved_cas") or "",
                ingredient.get("concentration"), ingredient.get("regulation_type") or "—", status, reason,
            ))
    return rows


def make_xlsx(rows):
    sheet=ET.Element("worksheet",xmlns=SHEET_NS)
    columns=ET.SubElement(sheet,"cols")
    for index,width in enumerate((24,16,14,28,18,14,16,16,58),1):
        ET.SubElement(columns,"col",min=str(index),max=str(index),width=str(width),customWidth="1")
    data=ET.SubElement(sheet,"sheetData")
    for number,values in enumerate((HEADERS,*rows),1):
        record=ET.SubElement(data,"row",r=str(number))
        for column,value in enumerate(values):
            address=f"{chr(65+column)}{number}"
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                ET.SubElement(ET.SubElement(record,"c",r=address),"v").text=str(value)
            else:
                cell=ET.SubElement(record,"c",r=address,t="inlineStr")
                text=ET.SubElement(ET.SubElement(cell,"is"),"t")
                text.text="" if value is None else "".join(c for c in str(value) if c in "\t\n\r" or 32<=ord(c)<=0xD7FF or 0xE000<=ord(c)<=0xFFFD or 0x10000<=ord(c)<=0x10FFFF)
    ET.SubElement(sheet,"autoFilter",ref=f"A1:I{len(rows)+1}")

    output=BytesIO()
    with ZipFile(output,"w",ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml",'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        workbook.writestr("_rels/.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        workbook.writestr("xl/workbook.xml",'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="스크리닝 결과" sheetId="1" r:id="rId1"/></sheets></workbook>')
        workbook.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        workbook.writestr("xl/worksheets/sheet1.xml",ET.tostring(sheet,encoding="utf-8",xml_declaration=True))
    output.seek(0)
    return output
