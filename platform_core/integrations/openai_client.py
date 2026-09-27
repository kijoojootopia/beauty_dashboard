"""Responses API 공통 클라이언트. CSV 값 추측이나 법적 판정을 하지 않습니다."""
import json
from .http_client import setting, request_json, IntegrationError


def respond(instructions, data, schema=None, search=False):
    key=setting("OPENAI_API_KEY")
    if not key:
        raise IntegrationError("OPENAI_API_KEY를 입력해 주세요.")
    payload={"model":setting("OPENAI_MODEL","gpt-4.1-mini"),"instructions":instructions,
             "input":json.dumps(data,ensure_ascii=False),"store":False,"max_output_tokens":5000}
    if schema:
        payload["text"]={"format":{"type":"json_schema","name":"result","strict":True,"schema":schema}}
    if search:
        payload.update(tools=[{"type":"web_search"}],tool_choice="required",include=["web_search_call.action.sources"])
    result=request_json("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+key},body=payload,timeout=60)
    if result.get("status") not in {None,"completed"} or result.get("error"):
        raise IntegrationError("AI 응답이 완료되지 않았습니다. 잠시 후 다시 시도해 주세요.")
    text="".join(c.get("text","") for item in result.get("output",[]) if item.get("type")=="message" for c in item.get("content",[]) if c.get("type")=="output_text")
    return text,result


def json_result(text):
    try:
        value=text.strip()
        if value.startswith("```"):
            value=value.split("\n",1)[1].rsplit("```",1)[0]
        return json.loads(value)
    except (ValueError,IndexError):
        raise IntegrationError("AI 분류 결과의 형식을 확인할 수 없습니다. 입력을 확인해 주세요.") from None
