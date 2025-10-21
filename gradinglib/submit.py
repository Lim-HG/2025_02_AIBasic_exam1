# gradinglib/submit.py
import json
from typing import Any, Dict, Tuple, Optional
import requests
import hmac, hashlib, base64
from urllib.parse import urlencode

# 코랩 버튼 렌더링용
def _display_html(html: str):
    try:
        from IPython.display import HTML, display  # Colab/Jupyter에서만
        display(HTML(html))
    except Exception:
        # 노트북 환경이 아니면 무시
        pass

def make_signature(student_id: str, name: str, exam_code: str, score: float, secret: bytes | str) -> str:
    """
    Apps Script Code.gs 의 makeMessageForSig() 규약과 100% 동일:
    메시지:  "학번|이름|시험코드|점수"
    알고리즘: HMAC-SHA256 → Base64
    """
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
    exam_code: str,  # exam1 / exam2 / exam3
    score: float,
    feedback: str = "",
) -> str:
    """
    제출 페이지(doGet) URL을 생성해 돌려줍니다. (HMAC 서명 포함)
    """
    sig = make_signature(student_id, name, exam_code, score, secret)
    params = {
        "student_id": student_id,
        "name": name,
        "exam_code": exam_code,
        "score": score,
        "feedback": feedback,
        "sig": sig,
    }
    return webapp_url.rstrip("?") + "?" + urlencode(params, encoding="utf-8", doseq=True)

def show_submit_button(
    webapp_url: str,
    secret: bytes | str,
    *,
    student_id: str,
    name: str,
    exam_code: str,
    score: float,
    feedback: str = "",
    title: str = "채점 완료",
) -> str:
    """
    코랩/주피터에서 '제출 페이지 열기' 버튼을 렌더링합니다.
    반환값: 생성된 URL (로그/테스트 용)
    """
    url = build_submit_url(
        webapp_url, secret,
        student_id=student_id, name=name, exam_code=exam_code,
        score=score, feedback=feedback
    )
    html = f"""
    <div style="font-family:system-ui; padding:12px; border:1px solid #eee; border-radius:12px;">
      <h3 style="margin:0 0 8px 0;">{title}</h3>
      <div>시험코드: <b>{exam_code}</b></div>
      <div>점수: <b>{score}</b></div>
      <div style="white-space:pre-line; color:#444; margin-top:6px;">피드백: {feedback}</div>
      <hr/>
      <p><b>마지막 단계:</b> 아래 버튼을 눌러 <u>학교 계정으로 1회 제출</u>하세요. (시험코드별 1회)</p>
      <a href="{url}" target="_blank"
         style="display:inline-block; padding:10px 14px; border-radius:8px; text-decoration:none; border:1px solid #ccc;">
         제출 페이지 열기
      </a>
    </div>
    """
    _display_html(html)
    return url

# ---------------- 기존 서버→서버 POST (필요 시 유지) ----------------

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
        try:
