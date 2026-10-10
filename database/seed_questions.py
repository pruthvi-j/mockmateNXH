import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymysql
from backend.question_bank import QUESTION_STORE

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='', database='nexthire_db')

with conn.cursor() as cur:
    for q in QUESTION_STORE:
        cur.execute(
            """
            INSERT INTO question_bank (id, question_code, target_role, category, difficulty, question_text, reference_answer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                question_code = VALUES(question_code),
                target_role = VALUES(target_role),
                category = VALUES(category),
                difficulty = VALUES(difficulty),
                question_text = VALUES(question_text),
                reference_answer = VALUES(reference_answer)
            """,
            (
                q["id"],
                q["question_code"],
                q["target_role"],
                q["category"],
                q["difficulty"].lower(),
                q["question_text"],
                q["reference_answer"]
            )
        )
conn.commit()
conn.close()
print("Question bank seeded into MySQL successfully!")
