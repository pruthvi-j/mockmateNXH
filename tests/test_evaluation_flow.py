"""
NextHire - Voice Interview & Post-Session Concept Evaluation Test
Tests:
1. Full session completion with spoken answers & skipped questions
2. No premature scoring during the interview
3. Post-session concept-based evaluation:
   - Technical quality via concept coverage (not exact wording)
   - Session communication score
   - Observable confidence score
   - Question-wise breakdown (identifying expected vs found concepts)
   - Proper handling of skipped questions (neither right nor wrong, 0 in score)
   - Accurate answered percentage
4. Strict session isolation (Session 1 Python vs Session 2 Java)
"""
import unittest
import io
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app

class TestEvaluationFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_complete_interview_and_post_session_evaluation(self):
        # 1. Initialize Session
        res_init = self.client.post("/api/interview/init")
        s_code = res_init.get_json()["session_code"]

        # 2. Upload Resume
        resume_data = "Skills: Python, Flask, Django, SQL, REST APIs, Microservices"
        file_tuple = (io.BytesIO(resume_data.encode("utf-8")), "candidate_resume.pdf")
        self.client.post("/api/interview/upload-resume", data={"session_code": s_code, "resume": file_tuple}, content_type="multipart/form-data")

        # 3. Select Role
        self.client.post("/api/interview/select-role", json={"session_code": s_code, "target_role": "Python Developer"})

        # 4. Start Round
        res_start = self.client.post("/api/interview/start-round", json={"session_code": s_code})
        data_start = res_start.get_json()
        self.assertTrue(data_start["success"])
        q1 = data_start["first_question"]
        self.assertEqual(q1["question_code"], "PL001")

        # 5. Answer Question 1 (Concept-rich answer, not exact text)
        q1_user_answer = (
            "Python manages memory automatically using a private heap. "
            "Its primary mechanism is reference counting, where an object is freed when references reach zero. "
            "It also has a cyclic garbage collector to detect and reclaim circular references across generations."
        )
        res_ans1 = self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q1["id"],
            "transcript_text": q1_user_answer,
            "status": "answered"
        })
        self.assertEqual(res_ans1.status_code, 200)
        data_ans1 = res_ans1.get_json()
        self.assertFalse(data_ans1["is_completed"])
        q2 = data_ans1["next_question"]
        self.assertEqual(q2["question_code"], "PL002")

        # 6. Skip Question 2
        res_ans2 = self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q2["id"],
            "transcript_text": "",
            "status": "skipped"
        })
        self.assertEqual(res_ans2.status_code, 200)
        data_ans2 = res_ans2.get_json()
        self.assertFalse(data_ans2["is_completed"])
        q3 = data_ans2["next_question"]
        self.assertEqual(q3["question_code"], "PL003")

        # 7. Answer Question 3
        q3_user_answer = (
            "Flask is a lightweight micro-framework allowing developers full freedom to choose an ORM like SQLAlchemy. "
            "In contrast, Django follows a batteries-included MVT structure with a built-in ORM and admin interface."
        )
        res_ans3 = self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q3["id"],
            "transcript_text": q3_user_answer,
            "status": "answered"
        })
        self.assertEqual(res_ans3.status_code, 200)
        data_ans3 = res_ans3.get_json()
        # All 3 questions processed!
        self.assertTrue(data_ans3["is_completed"])

        # 8. Post-Interview Evaluation
        res_eval = self.client.post("/api/interview/evaluate", json={"session_code": s_code})
        self.assertEqual(res_eval.status_code, 200)
        eval_report = res_eval.get_json()["report"]

        # Verify Counts & Percentage
        self.assertEqual(eval_report["total_questions"], 3)
        self.assertEqual(eval_report["answered_count"], 2)
        self.assertEqual(eval_report["skipped_count"], 1)
        self.assertAlmostEqual(eval_report["answered_percentage"], 66.7, delta=0.5)

        # Verify Scores (0 to 5.0)
        self.assertGreaterEqual(eval_report["technical_score"], 3.5)
        self.assertGreaterEqual(eval_report["communication_score"], 3.0)
        self.assertGreaterEqual(eval_report["confidence_score"], 2.5)
        self.assertGreaterEqual(eval_report["overall_score"], 3.0)

        # Verify Question Breakdown
        q_evals = eval_report["question_evaluations"]
        self.assertEqual(len(q_evals), 3)

        # Q1 Evaluation
        self.assertEqual(q_evals[0]["question_code"], "PL001")
        self.assertEqual(q_evals[0]["status"], "answered")
        self.assertEqual(q_evals[0]["concept_match"], "Strong concept match")
        self.assertIn("memory management", [c.lower() for c in q_evals[0]["concepts_identified"]])
        self.assertIn("garbage collection", [c.lower() for c in q_evals[0]["concepts_identified"]])

        # Q2 Evaluation (Skipped)
        self.assertEqual(q_evals[1]["question_code"], "PL002")
        self.assertEqual(q_evals[1]["status"], "skipped")
        self.assertEqual(q_evals[1]["concept_match"], "Skipped")
        self.assertIsNone(q_evals[1]["technical_score"])

        # Q3 Evaluation
        self.assertEqual(q_evals[2]["question_code"], "PL003")
        self.assertEqual(q_evals[2]["status"], "answered")
        self.assertEqual(q_evals[2]["concept_match"], "Strong concept match")

        # 9. Verify Feedback Retrieval API
        res_fb = self.client.get(f"/api/interview/feedback/{s_code}")
        self.assertEqual(res_fb.status_code, 200)
        fb_data = res_fb.get_json()["feedback"]
        self.assertEqual(fb_data["session_code"], s_code)
        self.assertEqual(fb_data["target_role"], "Python Developer")
        self.assertEqual(len(fb_data["strengths"]), len(eval_report["strengths"]))

    def test_strict_session_isolation(self):
        """
        Verify that Session 1 and Session 2 evaluations never leak into each other.
        """
        # Session A: Python
        sA = self.client.post("/api/interview/init").get_json()["session_code"]
        fA = (io.BytesIO(b"Skills: Python"), "resA.pdf")
        self.client.post("/api/interview/upload-resume", data={"session_code": sA, "resume": fA}, content_type="multipart/form-data")
        self.client.post("/api/interview/select-role", json={"session_code": sA, "target_role": "Python Developer"})
        rA = self.client.post("/api/interview/start-round", json={"session_code": sA}).get_json()
        qA = rA["first_question"]
        self.client.post("/api/interview/submit-answer", json={
            "session_code": sA, "question_id": qA["id"], "transcript_text": "Python memory management and garbage collection.", "status": "answered"
        })
        repA = self.client.post("/api/interview/evaluate", json={"session_code": sA}).get_json()["report"]

        # Session B: Java
        sB = self.client.post("/api/interview/init").get_json()["session_code"]
        fB = (io.BytesIO(b"Skills: Java, Spring"), "resB.pdf")
        self.client.post("/api/interview/upload-resume", data={"session_code": sB, "resume": fB}, content_type="multipart/form-data")
        self.client.post("/api/interview/select-role", json={"session_code": sB, "target_role": "Java Developer"})
        rB = self.client.post("/api/interview/start-round", json={"session_code": sB}).get_json()
        qB = rB["first_question"]
        # Skip question in Session B
        self.client.post("/api/interview/submit-answer", json={
            "session_code": sB, "question_id": qB["id"], "transcript_text": "", "status": "skipped"
        })
        repB = self.client.post("/api/interview/evaluate", json={"session_code": sB}).get_json()["report"]

        # Assert isolation between Session A and Session B
        self.assertNotEqual(sA, sB)
        self.assertEqual(repA["target_role"], "Python Developer")
        self.assertEqual(repB["target_role"], "Java Developer")
        self.assertNotEqual(repA["skipped_count"], repB["skipped_count"])

        # Fetch independently via endpoint
        fbA = self.client.get(f"/api/interview/feedback/{sA}").get_json()["feedback"]
        fbB = self.client.get(f"/api/interview/feedback/{sB}").get_json()["feedback"]

        self.assertEqual(fbA["session_code"], sA)
        self.assertEqual(fbB["session_code"], sB)
        self.assertEqual(fbA["target_role"], "Python Developer")
        self.assertEqual(fbB["target_role"], "Java Developer")

if __name__ == "__main__":
    unittest.main()
