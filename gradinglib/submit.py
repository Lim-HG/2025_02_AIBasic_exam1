import requests # requests 라이브러리 사용
import json

def save_result_via_appsscript(student_id, name, score, feedback, app_script_url):
    """채점 결과를 Apps Script 웹 앱으로 전송합니다."""
    try:
        # 전송할 데이터를 JSON 형식으로 준비
        payload = {
            "student_id": student_id,
            "name": name,
            "score": score,
            "feedback": feedback
        }
        
        # POST 요청 보내기
        response = requests.post(app_script_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status() # 오류가 있으면 예외 발생
        
        # 응답 결과 반환
        return f"Google Sheet에 결과가 전송되었습니다. (응답: {response.json()})"

    except requests.exceptions.RequestException as e:
        return f"Apps Script로 결과 전송 중 오류 발생: {e}"
