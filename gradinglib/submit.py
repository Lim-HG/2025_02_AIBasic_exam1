# gradinglib/submit.py
import json
from typing import Any, Dict, Tuple, Optional
import requests
import hmac, hashlib, base64
from urllib.parse import urlencode
import collections # 👈 [추가됨] 정렬된 딕셔너리(서명용)를 위해

# 코랩 버튼 렌더링용
def _display_html(html: str):
    try:
        from IPython.display import HTML, display  # Colab/Jupyter에서만
        display(HTML(html))
    except Exception:
        # 노트북 환경이 아니면 무시
        pass

# --- [새로 추가됨] Code.gs와 일치하는 JSON 서명 함수 ---
def _make_json_signature(payload: Dict[str, Any], secret: str | bytes) -> str:
    """
    Apps Script(Code.gs)의 서명 로직과 일치하는 HMAC-SHA256 서명을 생성합니다.
    """
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    
    # 1. 키 기준으로 정렬
    ordered_payload = collections.OrderedDict(sorted(payload.items()))
    
    # 2. JSON 문자열로 변환 (공백 없이)
    payload_string = json.dumps(ordered_payload, separators=(',', ':'), ensure_ascii=False)
    
    # 3. HMAC-SHA256 계산
    digest = hmac.new(secret, payload_string.encode("utf-8"), hashlib.sha256).digest()
    
    # 4. 16진수 문자열로 반환
    return digest.hex()


# --- [핵심 수정] 버튼 표시 대신 '직접 POST 제출'을 하도록 변경 ---
def show_submit_button(
    webapp_url: str,
    secret: bytes | str,
    *,
    student_id: str,
    name: str,
    exam_code: str,
    score: float,          # ✅ 최종점수
    feedback: str = "",
    title: str = "채점 완료",
) -> str:
    """
    [수정됨] 
    HTML 버튼을 표시하는 대신, 서버(Apps Script)로 직접 POST 요청을 전송하고
    그 결과를 HTML로 표시합니다.
    """
    
    # 1. 서명할 데이터 준비 (sig 자체는 제외)
    payload_data = {
        "student_id": str(student_id).strip(),
        "name": str(name).strip(),
        "exam_code": exam_code,
        "score": score,
        "feedback": feedback,
    }

    # 2. 서명 생성
    try:
        sig = _make_json_signature(payload_data, secret)
    except Exception as e:
        error_html = f"<h3>❌ 서명 생성 오류</h3><p>로컬에서 서명을 생성하는 중 오류가 발생했습니다: {e}</p>"
        _display_html(error_html)
        return f"[Debug] Signature generation error: {e}"

    # 3. 전송할 전체 페이로드 (데이터 + 서명)
    full_payload = {
        **payload_data,
        "sig": sig
    }

    # 4. Apps Script로 직접 POST 요청 전송
    html_result = ""
    debug_message = ""
    
    # [삭제됨]
    # '학번/이름 미입력 방지' if 블록이 여기서 삭제되었습니다.
    # 이제 "None" 값도 서버로 그대로 전송됩니다.

    try:
        r = requests.post(
            webapp_url,
            json=full_payload,  # data= 대신 json= 사용
            headers={"Content-Type": "application/json"},
            timeout=20, # 20초 타임아웃
        )
        r.raise_for_status() # 4xx, 5xx 오류 발생 시 예외 발생
        
        # 5. Code.gs로부터 받은 JSON 응답 파싱
        res = r.json()
        message = res.get("message", "알 수 없는 응답입니다.")

        if res.get("ok") is True:
            # [성공]
            html_result = f"""
            <div style="font-family:system-ui; padding:12px; border:1px solid #137333; background: #e6f4ea; border-radius:12px;">
                <h3 style="margin:0 0 8px 0; color: #137333;">✅ 제출 완료</h3>
                <div><b>시험코드:</b> {exam_code}</div>
                <div><b>학번/이름:</b> {student_id} / {name}</div>
                <div><b>점수:</b> {score}</div>
                <p style="color:#137333; margin-top:8px;"><b>{message}</b></p>
            </div>
            """
            debug_message = f"[Success] {message}"
        else:
            # [실패] (중복 제출, 로그인 오류 등)
            reason = res.get("reason", "unknown_error")
            html_result = f"""
            <div style="font-family:system-ui; padding:12px; border:1px solid #b00020; background: #fce8e6; border-radius:12px;">
                <h3 style="margin:0 0 8px 0; color: #b00020;">❌ 제출 실패</h3>
                <div><b>시험코드:</b> {exam_code}</div>
                <p style="color:#b00020; margin-top:8px;"><b>오류: {message}</b> (코드: {reason})</p>
            </div>
            """
            debug_message = f"[Failed] Reason: {reason}, Message: {message}"

    except requests.exceptions.HTTPError as e:
        html_result = f"<h3>❌ HTTP 오류</h3><p>서버가 오류를 반환했습니다: {e}. (응답: {e.response.text})</p>"
        debug_message = f"[Debug] HTTP error: {e}"
    except requests.exceptions.Timeout:
        html_result = "<h3>❌ 시간 초과</h3><p>서버에 연결하는 데 시간이 너무 오래 걸립니다.</p>"
        debug_message = "[Debug] Request Timeout"
    except requests.exceptions.RequestException as e:
        html_result = f"<h3>❌ 네트워크 오류</h3><p>서버에 연결할 수 없습니다: {e}</p>"
        debug_message = f"[Debug] Network error: {e}"
    except Exception as e:
        html_result = f"<h3>❌ 알 수 없는 오류</h3><p>제출 중 예기치 않은 오류가 발생했습니다: {e}</p>"
        debug_message = f"[Debug] Unknown error: {e}"

    # 6. Colab에 결과 HTML 표시
    _display_html(html_result)
    
    # 7. __init__.py로 디버그 메시지 반환 (Colab 셀에 출력됨)
    return debug_message

# ------------------------------------------------------------------
#  ▼ 아래 함수들은 새 방식(POST)에서는 사용되지 않지만,
#    (혹시 모를 호환성을 위해) 그대로 둡니다.
# ------------------------------------------------------------------

def make_signature(student_id: str, name: str, exam_code: str, score: float, secret: bytes | str) -> str:
    # (구 방식 서명 로직)
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    msg = f"{student_id}|{name}|{exam_code}|{score}"
    digest = hmac.new(secret, msg.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")

def build_submit_url(
    webapp_url: str,
    secret: bytes | str,
    *,
    student_id: str,
    name: str,
    exam_code: str,
    score: float,          # ✅ 최종점수
    feedback: str = "",
) -> str:
    # (구 방식 URL 빌드 로직)
    sig = make_signature(student_id, name, exam_code, score, secret)
    params = {
        "student_id": student_id,
        "name": name,
        "exam_code": exam_code,
        "score": score,    # ✅ 최종점수 그대로 전송
        "feedback": feedback,
        "sig": sig,
    }
    return webapp_url.rstrip("?") + "?" + urlencode(params, encoding="utf-8", doseq=True)


# ---------------- 기존 서버→서버 POST (필요 시 유지) ----------------
# (이하 `_normalize_response` 및 `save_result_via_appsscript` 함수는
#  수정 없이 그대로 둡니다.)
# ------------------------------------------------------------------

def _normalize_response(res: Dict[str, Any]) -> Tuple[str, str]:
    if "ok" in res:
        if res.get("ok") is True:
            return "success", ""
        reason = str(res.get("reason", "")).strip().lower()
        if reason == "already_submitted":
            return "already_submitted", reason or "already_submitted"
        return "error", reason
    if "status" in res:
        status = str(res.get("status", "")).strip().lower()
        reason = str(res.get("reason") or "").strip().lower()
        if status == "success":
            return "success", ""
        if reason == "already_submitted":
            return "already_submitted", reason
        if status == "error":
            return "error", reason
    return "error", ""

def save_result_via_appsscript(
    student_id: str,
    name: str,
    score: float,
    feedback: str,
    app_script_url: str,
    assignment: str = "MLDL-2",
    email: str = "",
    *,
    api_key: str = "",
    target: str = "score",
    timeout: int = 15,
) -> str:
    payload: Dict[str, Any] = {
        "student_id": student_id,
        "name": name,
        "score": score,
        "feedback": feedback,
        "assignment": assignment,
        "target": target,
    }
    if email:
        payload["email"] = email
    if api_key:
        payload["api_key"] = api_key

    try:
        r = requests.post(
            app_script_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        r.raise_for_status()

        # JSON 파싱
        try:
            res = r.json()
        except ValueError:
            body_preview = (r.text or "").strip()
            if len(body_preview) > 300:
                body_preview = body_preview[:300] + "...(truncated)"
            return f"[전송실패] 응답이 JSON 형식이 아닙니다: {body_preview}"

        # 표준화된 상태 판정
        status, reason = _normalize_response(res)

        if status == "success":
            return f"[저장완료] {assignment} / {student_id}"

        if status == "already_submitted":
            return "[재제출차단] 이미 제출된 기록이 있어 저장되지 않았습니다."

        # 그 밖의 에러: 서버 메시지 함께 노출
        msg = res.get("message") or res.get("detail") or res.get("error") or res
        return f"[전송실패] {msg}"

    except requests.exceptions.Timeout:
        return "[전송실패] 네트워크 지연으로 시간 초과되었습니다.(timeout)"
    except requests.exceptions.HTTPError as e:
        # HTTP 오류의 응답 본문 프리뷰
        body_preview = ""
        try:
            body_preview = r.text.strip()
            if len(body_preview) > 300:
                body_preview = body_preview[:300] + "...(truncated)"
        except Exception:
            pass
        return f"[전송실패] HTTP 오류: {e}; 응답 본문: {body_preview}"
    except requests.exceptions.RequestException as e:
        return f"[전송실패] 네트워크/요청 오류: {e}"
    except Exception as e:
        return f"[전송실패] 처리 중 예외: {e}"
