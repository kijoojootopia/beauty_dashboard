"""CSV 내용/열 의미 인식. 외부 AI는 열 위치만 선택하며 원본 값은 변경하지 않습니다."""
import csv
import io
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

CAS = re.compile(r'^\d{2,7}-\d{2}-\d$')
FIELDS=('inci_name','cas_no','concentration')


def percentage(value):
    if value is None or str(value).strip()=='': return None
    if isinstance(value,bool): raise ValueError('함량에 참/거짓을 사용할 수 없습니다.')
    text=unicodedata.normalize('NFKC',str(value)).strip().removesuffix('%').strip()
    if re.fullmatch(r'\d+,\d+',text): text=text.replace(',','.')
    try: number=Decimal(text)
    except InvalidOperation: raise ValueError('함량은 0~100의 숫자(%)여야 합니다.') from None
    if not number.is_finite() or not 0<=number<=100: raise ValueError('함량은 0~100의 유한한 숫자(%)여야 합니다.')
    return float(number)


def field_hint(value):
    text=re.sub(r'[\W_]+','',str(value).casefold())
    if 'cas' in text or '카스' in text: return 'cas_no'
    if any(w in text for w in ('concentr','percent','함량','배합','함유','농도','비율','ratio','content','wt')) or '%' in str(value): return 'concentration'
    if any(w in text for w in ('inci','ingredient','성분','원료','물질','원재료','성분명')) or text in ('name','명칭'): return 'inci_name'
    return None


def normalize_row(raw):
    if not isinstance(raw,dict): raise ValueError('성분 행은 객체여야 합니다.')
    row={k:raw.get(k,'') for k in FIELDS}
    for key,value in raw.items():
        hint=field_hint(key)
        if hint and hint not in raw: row[hint]=value
    for key in ('inci_name','cas_no'): row[key]=str(row[key] or '').strip()
    if not row['inci_name'] and not row['cas_no']: raise ValueError('성분명 또는 CAS가 필요합니다.')
    if len(row['inci_name'])>500 or len(row['cas_no'])>100: raise ValueError('성분명은 500자, CAS는 100자 이내로 입력해 주세요.')
    row['concentration']=percentage(row['concentration'])
    return row


def read_table(content):
    if isinstance(content,bytes):
        if len(content)>2*1024*1024: raise ValueError('CSV는 2MB까지 입력할 수 있습니다.')
        for encoding in ('utf-8-sig','utf-16' if content.startswith((b'\xff\xfe',b'\xfe\xff')) else 'cp949'):
            try: text=content.decode(encoding);break
            except UnicodeError: pass
        else: raise ValueError('CSV를 UTF-8 또는 CP949로 저장해 주세요.')
    else: text=str(content).lstrip('\ufeff')
    try:
        dialect=csv.Sniffer().sniff(text[:16000],delimiters=',;\t|')
        table=list(csv.reader(io.StringIO(text),dialect))
    except csv.Error:
        # 일반 쉼표 CSV의 열 불일치도 아래에서 검사합니다.
        table=list(csv.reader(io.StringIO(text)))
    table=[[v.strip() for v in row] for row in table if any(v.strip() for v in row)]
    if not table: raise ValueError('CSV에 성분 데이터가 없습니다.')
    width=len(table[0])
    if width>30 or any(len(row)!=width for row in table): raise ValueError('CSV 열 개수를 확인하세요. 쉼표가 있는 성분명은 큰따옴표로 감싸세요.')
    if len(table)>501: raise ValueError('성분을 최대 500개까지 입력할 수 있습니다.')
    return table


def infer_columns(table, use_ai=False):
    first=table[0]
    hints=[field_hint(x) for x in first]
    # 숫자/CAS가 있으면 첫 줄도 성분 행일 가능성이 큽니다.
    has_header=any(hints) and not any(CAS.fullmatch(v) or re.fullmatch(r'\d+(?:[.,]\d+)?%?',v) for v in first)
    if not has_header and len(table)>1:
        has_header=all(not CAS.fullmatch(v) and not re.fullmatch(r'\d+(?:[.,]\d+)?%?',v) for v in first) and any(CAS.fullmatch(v) for v in table[1])
    mapping={k:None for k in FIELDS}
    if has_header:
        if len(first)!=len(set(first)): raise ValueError('CSV에 중복 열 이름이 있습니다.')
        for key in FIELDS:
            candidates=[i for i,h in enumerate(hints) if h==key]
            if len(candidates)==1: mapping[key]=candidates[0]
    data=table[1:] if has_header else table
    if not data: raise ValueError('CSV에 성분 데이터 행이 없습니다.')
    profiles=[]
    for i in range(len(first)):
        values=[row[i] for row in data if row[i]]
        cas=bool(values) and all(CAS.fullmatch(v) for v in values)
        numeric=bool(values) and all(re.fullmatch(r'\d+(?:[.,]\d+)?\s*%?',v) for v in values)
        profiles.append((cas,numeric))
    for key in FIELDS:
        if mapping[key] is not None: continue
        used=set(mapping.values())
        choices=[]
        for i,(cas,numeric) in enumerate(profiles):
            if i in used: continue
            if has_header and re.search(r'순번|번호|^no\.?$|^id$|^index$|비고|설명|용도|function',first[i],re.I): continue
            if key=='cas_no' and cas: choices.append(i)
            if key=='concentration' and numeric: choices.append(i)
            if key=='inci_name' and not cas and not numeric and any(r[i] for r in data): choices.append(i)
        if len(choices)==1: mapping[key]=choices[0]
    if use_ai:
        from ..integrations.ingredient_ai import classify_columns
        proposed=classify_columns(table)
        has_header=proposed['has_header']
        mapping={k:proposed[k] for k in FIELDS}
    return has_header,mapping


def table_rows(table, has_header, mapping):
    width=len(table[0])
    used=[v for v in mapping.values() if v is not None]
    if any(type(v) is not int or v<0 or v>=width for v in used) or len(set(used))!=len(used): raise ValueError('각 열은 한 항목에만 지정해 주세요.')
    if mapping.get('inci_name') is None and mapping.get('cas_no') is None: raise ValueError('성분명 또는 CAS 열을 선택해 주세요.')
    data=table[1:] if has_header else table
    if len(data)>500: raise ValueError('성분을 최대 500개까지 입력할 수 있습니다.')
    return [normalize_row({k:row[mapping[k]] if mapping.get(k) is not None else '' for k in FIELDS}) for row in data]


def parse_csv(content):
    table=read_table(content)
    has_header,mapping=infer_columns(table)
    if mapping['inci_name'] is None and mapping['cas_no'] is None:
        raise ValueError('열을 확정할 수 없습니다. 성분 자동 분류에서 열을 선택해 주세요.')
    if mapping['concentration'] is None and any(re.fullmatch(r'\d+(?:[.,]\d+)?%?',v) for row in table[1:] for v in row):
        raise ValueError('배합 비율 열을 확인해 주세요. 성분 자동 분류에서 지정할 수 있습니다.')
    return table_rows(table,has_header,mapping)


def parse_text(text):
    rows=[]
    for line in re.split(r'[;\n]+',text):
        if not line.strip(): continue
        cells=line.strip().split('\t')
        if len(cells)==1: raw={'inci_name':cells[0]}
        elif len(cells)==2: raw={'inci_name':cells[0], 'cas_no' if CAS.fullmatch(cells[1]) else 'concentration':cells[1]}
        elif len(cells)==3: raw=dict(zip(FIELDS,cells))
        else: raise ValueError('성분명, CAS, 함량을 탭으로 구분해 주세요.')
        rows.append(normalize_row(raw))
    return rows
