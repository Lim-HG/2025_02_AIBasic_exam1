import csv
import os

def save_result(student_id, name, score, feedback, outdir="results"):
    os.makedirs(outdir, exist_ok=True)
    filepath = os.path.join(outdir, f"{student_id}_{name}.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["학번", "이름", "점수", "피드백"])
        writer.writerow([student_id, name, score, feedback])
    return filepath