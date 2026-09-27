import io
import pytest
from conftest import post,signup
from tab1_regulation.services.ingredient_parser import parse_csv,infer_columns,read_table,table_rows

@pytest.mark.parametrize('csv',[
 '배합 비율,원료 이름,cas 번호\n80%,정제수,7732-18-5\n5%,글리세린,56-81-5',
 'CAS Registry;INCI Name;Weight percent\n7732-18-5;Water;80\n56-81-5;Glycerin;5',
 '7732-18-5\tWater\t80\n56-81-5\tGlycerin\t5',
 '성분명,함량,CAS\n정제수,80,7732-18-5\n글리세린,5,56-81-5'.encode('cp949'),
])
def test_flexible_columns_and_encodings(csv):
    rows=parse_csv(csv)
    assert len(rows)==2 and rows[0]['cas_no']=='7732-18-5' and rows[1]['concentration']==5


def test_decimal_comma_and_no_serial_as_percent():
    rows=parse_csv('No;성분명;CAS;배합 비율\n1;Water;7732-18-5;95,5\n2;Glycerin;56-81-5;4,5')
    assert rows[0]['concentration']==95.5
    header,mapping=infer_columns(read_table('순번,성분명,용도\n1,Water,용매\n2,Glycerin,보습'))
    assert mapping['concentration'] is None
    with pytest.raises(ValueError): table_rows([['Water','80']],False,{'inci_name':0,'concentration':0})


def test_preview_is_authenticated_and_ai_changes_columns_only(client,monkeypatch):
    assert client.post('/api/ingredients/preview').status_code==400
    signup(client)
    monkeypatch.setattr('tab1_regulation.integrations.ingredient_ai.classify_columns',lambda table:{'has_header':True,'inci_name':1,'cas_no':0,'concentration':2})
    response=post(client,'/api/ingredients/preview',{'ingredients_csv':(io.BytesIO(b'identifier,material,amount\n7732-18-5,Water,80'),'test.csv'),'use_ai':'1'})
    assert response.status_code==200 and response.json['ingredients'][0]=={'inci_name':'Water','cas_no':'7732-18-5','concentration':80.0}
