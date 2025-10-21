import requests, json

def save_result_via_appsscript(student_id, name, score, feedback,
                               app_script_url, assignment="MLDL-2",
                               email="", api_key=""):
    """Google Apps Script 웹앱으로 채점 결과를 전송하는 함수"""

    # 전송할 데이터
    payload = {
        "student_id": student_id,
        "name": name,
        "score": score,
        "feedback": feedback,
        "assignment": assignment
    }

    # 선택적 보조 필드
    if email:
        payload["email"] = email

    # ★ 추가된 부분: API 키를 body에 포함
    if api_key:
        payload["api_key"] = api_key

    # Apps Script에 전송
    r = requests.post(
        app_script_url,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json'},
        timeout=15
    )

    r.raise_for_status()
    res = r.json()

    # 결과 메시지 처리
    if res.get("ok"):
        return f"[저장완료] {assignment} / {student_id}"
    elif res.get("reason") == "already_submitted":
        return f"[재제출차단] 이미 제출된 기록이 있어 저장되지 않았습니다."
    elif res.get("reason") == "unauthorized":
        return f"[전송실패] 인증 실패(API 키 불일치)"
    else:
        return f"[전송실패] {res}"
