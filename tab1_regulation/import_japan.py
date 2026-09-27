"""사용자 제공 JSON을 원문 구조 그대로 설치하는 로컬 명령."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

FILES={"japan_prohibit.json":"prohibited_ingredients.json", "japan_restrict.json":"restricted_ingredients.json", "japan_cosmetics_export_roadmap.json":"pipeline_checklist.json"}

def import_files(source_dir,target_dir,replace=False):
    prepared=[]
    for source_name,target_name in FILES.items():
        raw=(Path(source_dir)/source_name).read_bytes()
        data=json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data,list) or not data or any(not isinstance(row,dict) for row in data):
            raise ValueError(f"{source_name}: 비어 있지 않은 객체 배열이 필요합니다.")
        if target_name=="pipeline_checklist.json":
            if any(not all(k in r for k in ["stage_step","task_id","task_name"]) for r in data):
                raise ValueError("로드맵 필드를 확인해 주세요.")
        elif any(not (r.get("inci_name") or r.get("cas_no")) for r in data):
            raise ValueError("성분명 또는 CAS 필드를 확인해 주세요.")
        target=Path(target_dir)/target_name
        if target.exists() and json.loads(target.read_text(encoding="utf-8-sig")) and not replace:
            raise ValueError(f"{target_name}에 기존 데이터가 있습니다. 교체하려면 --replace를 지정하세요.")
        prepared.append((target,raw))
    Path(target_dir).mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(b"".join(raw for _,raw in prepared)).hexdigest()
    for target,raw in prepared:
        target.write_bytes(raw)
    metadata={"version":"user-japan-"+digest[:12],"reviewed_at":None,"source":"일본 후생노동성 「Standards for Cosmetics」 · 사용자 제공 자료, 최신 개정 미검토", "source_url":None,"last_collected_at":None,"imported_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"complete_lists":{"prohibited":True,"restricted":True}}
    (Path(target_dir)/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return digest

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="일본 성분·로드맵 JSON 3개를 설치합니다. 기존 비어 있지 않은 데이터는 기본적으로 보존합니다.")
    parser.add_argument("--source-dir",required=True,help="japan_*.json 원본 3개가 들어 있는 폴더")
    parser.add_argument("--replace",action="store_true",help="기존 일본 데이터의 명시적 교체")
    args=parser.parse_args()
    try:
        digest=import_files(args.source_dir,Path(__file__).parent/"data/jp",args.replace)
    except (OSError,ValueError) as error:
        parser.exit(1,str(error)+"\n")
    print("일본 데이터 3개를 설치했습니다. 검토일은 미등록 상태입니다. 데이터 해시:",digest[:12])
