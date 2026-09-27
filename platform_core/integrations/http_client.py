"""공개 HTTP/캐시 계약. 키·응답 원문을 오류 메시지나 로그에 노출하지 않습니다."""
import hashlib
import json
import os
import re
import socket
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, unquote
from urllib.request import Request, urlopen
from flask import current_app, has_app_context
from dotenv import dotenv_values


class IntegrationError(ValueError):
    pass


def setting(name, default=""):
    if has_app_context():
        if name in current_app.config:
            return current_app.config[name]
        if current_app.testing and not current_app.config.get("ENABLE_EXTERNAL_APIS"):
            return default
        # .env 키 수정은 다음 요청부터 반영합니다. 테스트는 실제 키를 읽지 않습니다.
        values=dotenv_values(Path(current_app.root_path).parent/".env")
        if name in values:
            return values[name] or default
    return os.environ.get(name, default)


def request_bytes(url, params=None, headers=None, body=None, timeout=15):
    params=dict(params or {})
    for name in ("serviceKey",):
        if name in params:
            params[name]=unquote(str(params[name]))
    if params:
        url += ("&" if "?" in url else "?")+urlencode(params)
    request=Request(url,headers={"User-Agent":"BeautyDashboard/1.1","Accept":"application/json, application/xml",**(headers or {})},
                    data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None)
    if body is not None:
        request.add_header("Content-Type","application/json")
    try:
        with urlopen(request,timeout=timeout) as response:
            data=response.read(12*1024*1024+1)
        if len(data)>12*1024*1024:
            raise IntegrationError("API 응답이 너무 큽니다. 조회 범위를 줄여 주세요.")
        return data
    except HTTPError as error:
        labels={401:"인증키를 확인해 주세요.",403:"키와 해당 API 이용 승인을 확인해 주세요.",429:"호출 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."}
        raise IntegrationError(f"API HTTP {error.code} · "+labels.get(error.code,"제공처 응답을 확인해 주세요.")) from None
    except (URLError,TimeoutError,socket.timeout,OSError):
        raise IntegrationError("API 연결 시간이 초과되었거나 제공처에 연결할 수 없습니다.") from None


def request_json(url, **kwargs):
    try:
        return json.loads(request_bytes(url,**kwargs))
    except (UnicodeError,json.JSONDecodeError):
        raise IntegrationError("API 응답이 올바른 JSON 형식이 아닙니다.") from None


def hs_codes():
    codes=list(dict.fromkeys(c.strip() for c in str(setting("COSMETICS_HS_CODES","3304")).split(",") if c.strip()))
    if not codes or len(codes)>20 or any(not re.fullmatch(r"\d{4}|\d{6}",c) for c in codes):
        raise IntegrationError("COSMETICS_HS_CODES는 4/6자리 HS 코드를 쉼표로 구분해 주세요.")
    if any(a!=b and b.startswith(a) for a in codes for b in codes):
        raise IntegrationError("상위·하위 HS 코드를 함께 합산하면 중복됩니다. 품목 범위를 확인해 주세요.")
    return codes


_locks={}
_guard=threading.Lock()


def cached(namespace, criteria, loader, ttl=21600):
    digest=hashlib.sha256(json.dumps([namespace,criteria],sort_keys=True,default=str).encode()).hexdigest()
    directory=Path(current_app.config.get("API_CACHE_DIR",Path(current_app.config["DATABASE"]).parent/"api_cache"))
    path=directory/(digest+".json")
    with _guard:
        lock=_locks.setdefault(digest,threading.Lock())
    with lock:
        try:
            saved=json.loads(path.read_text(encoding="utf-8"))
            if time.time()-saved["time"]<ttl:
                if "error" in saved:
                    if time.time()-saved["time"]<60:
                        raise IntegrationError(saved["error"])
                else:
                    return saved["data"]
        except (OSError,UnicodeError,KeyError,json.JSONDecodeError):
            pass
        try:
            data=loader()
        except IntegrationError as error:
            _save_cache(path,{"time":time.time(),"error":str(error)})
            raise
        _save_cache(path,{"time":time.time(),"data":data})
        return data


def _save_cache(path, value):
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w",dir=path.parent,delete=False,encoding="utf-8") as f:
        json.dump(value,f,ensure_ascii=False)
    os.replace(f.name,path)
