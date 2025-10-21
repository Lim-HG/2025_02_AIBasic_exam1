import requests, json

def save_result_via_appsscript(student_id, name, score, feedback, app_script_url, assignment="MLDL-2", email=""):
    payload = {
        "student_id": student_id,
        "name": name,
        "score": score,
        "feedback": feedback,
        "assignment": assignment
    }
    if email:
        payload["email"] = email  # 외부 계정 환경 대비 보조 식별

    r = requests.post(app_script_url, data=json.dumps(payload),
                      headers={'Content-Type': 'application/json'})
    r.raise_for_status()
    res = r.json()
    if res.get("ok"):
        return f"[저장완료] {assignment} / {student_id}"
    elif res.get("reason") == "already_submitted":
        return f"[재제출차단] 이미 제출된 기록이 있어 저장되지 않았습니다."
    else:
        return f"[전송실패] {res}"
