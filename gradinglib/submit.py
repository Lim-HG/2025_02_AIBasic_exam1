import gspread
from google.oauth2.service_account import Credentials
import datetime

def save_result_to_sheet(student_id, name, score, feedback, sheet_name, creds_json_path):
    """채점 결과를 지정된 Google Sheet에 저장합니다."""
    try:
        # 인증 정보 설정
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_json_path, scopes=scopes)
        client = gspread.authorize(creds)

        # Google Sheet 열기
        sheet = client.open(sheet_name).sheet1

        # 헤더가 없으면 추가
        if not sheet.get_all_values():
            headers = ["Timestamp", "학번", "이름", "점수", "피드백"]
            sheet.append_row(headers)

        # 새 결과 행 추가
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [timestamp, student_id, name, score, feedback]
        sheet.append_row(new_row)

        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.spreadsheet.id}"
        return f"Google Sheet '{sheet_name}'에 저장되었습니다. URL: {sheet_url}"

    except Exception as e:
        return f"Google Sheet 저장 중 오류 발생: {e}"

# 기존의 CSV 저장 함수는 필요시 남겨두거나 삭제할 수 있습니다.
# def save_result(student_id, name, score, feedback, outdir="results"):
#     ...
