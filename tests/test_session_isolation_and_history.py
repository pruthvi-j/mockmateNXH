"""
NextHire - Session Isolation & History Verification Test Suite
Verifies:
  - Test A: Old completed interview (NXH-2026-MCA-01) retains 3 answered questions and valid scores.
  - Test B: Skipped interview (NXH-20261006-F48902) shows 0 answered, 3 skipped, N/A (None) scores.
  - Test C: Session switching isolates reports completely.
  - Test D: Page refresh / re-fetching retains original session data without cross-contamination.
  - Test E: History API returns accurate per-session statistics.
  - Test F: Partial interview (1 answered, 2 skipped) evaluates answered question and tracks skipped questions safely.
"""

import unittest
import json
from backend.app import create_app

class TestSessionIsolationAndHistory(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_A_old_completed_interview(self):
        """Test A: Verify historical completed Full Stack interview NXH-2026-MCA-01."""
        res = self.client.get("/api/interview/feedback/NXH-2026-MCA-01")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        fb = data["feedback"]
        
        self.assertEqual(fb["session_code"], "NXH-2026-MCA-01")
        self.assertEqual(fb["target_role"], "Full Stack Software Engineer")
        self.assertEqual(fb["total_questions"], 3)
        self.assertEqual(fb["answered_count"], 3)
        self.assertEqual(fb["skipped_count"], 0)
        self.assertEqual(fb["technical_score"], 4.5)
        self.assertEqual(fb["communication_score"], 3.9)
        self.assertEqual(fb["confidence_score"], 4.0)
        self.assertEqual(fb["overall_score"], 4.2)
        self.assertEqual(len(fb["question_evaluations"]), 3)
        for q_eval in fb["question_evaluations"]:
            self.assertEqual(q_eval["status"], "answered")

    def test_B_skipped_interview(self):
        """Test B: Verify zero-answer interview NXH-20261006-F48902."""
        res = self.client.get("/api/interview/feedback/NXH-20261006-F48902")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        fb = data["feedback"]

        self.assertEqual(fb["session_code"], "NXH-20261006-F48902")
        self.assertEqual(fb["target_role"], "Python Developer")
        self.assertEqual(fb["total_questions"], 3)
        self.assertEqual(fb["answered_count"], 0)
        self.assertEqual(fb["skipped_count"], 3)
        
        # Scores MUST be None due to insufficient evidence
        self.assertIsNone(fb["overall_score"])
        self.assertIsNone(fb["technical_score"])
        self.assertIsNone(fb["communication_score"])
        self.assertIsNone(fb["confidence_score"])
        
        # Verify limited evidence note
        self.assertIsNotNone(fb.get("limited_evidence_note"))
        
        # All question evaluations marked skipped
        self.assertEqual(len(fb["question_evaluations"]), 3)
        for q_eval in fb["question_evaluations"]:
            self.assertEqual(q_eval["status"], "skipped")
            self.assertIsNone(q_eval["technical_score"])

    def test_C_session_switching_isolation(self):
        """Test C: Switch between Full Stack and Python Developer reports and back."""
        # 1. Open Full Stack report
        res1 = self.client.get("/api/interview/feedback/NXH-2026-MCA-01")
        fb1 = res1.get_json()["feedback"]
        self.assertEqual(fb1["target_role"], "Full Stack Software Engineer")
        self.assertEqual(fb1["technical_score"], 4.5)

        # 2. Open Python Developer report
        res2 = self.client.get("/api/interview/feedback/NXH-20261006-F48902")
        fb2 = res2.get_json()["feedback"]
        self.assertEqual(fb2["target_role"], "Python Developer")
        self.assertIsNone(fb2["technical_score"])

        # 3. Return to Full Stack report
        res3 = self.client.get("/api/interview/feedback/NXH-2026-MCA-01")
        fb3 = res3.get_json()["feedback"]
        self.assertEqual(fb3["target_role"], "Full Stack Software Engineer")
        self.assertEqual(fb3["technical_score"], 4.5)

    def test_D_refresh_preserves_data(self):
        """Test D: Refreshing Python Developer feedback repeatedly returns exact same isolated data."""
        for _ in range(3):
            res = self.client.get("/api/interview/feedback/NXH-20261006-F48902")
            fb = res.get_json()["feedback"]
            self.assertEqual(fb["answered_count"], 0)
            self.assertEqual(fb["skipped_count"], 3)
            self.assertIsNone(fb["overall_score"])

    def test_E_history_api(self):
        """Test E: History endpoint lists all sessions with isolated stats."""
        res = self.client.get("/api/interview/history")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        history = data["history"]
        
        session_codes = [h["session_code"] for h in history]
        self.assertIn("NXH-2026-MCA-01", session_codes)
        self.assertIn("NXH-20261006-F48902", session_codes)

        # Find Full Stack item
        fs_item = next(h for h in history if h["session_code"] == "NXH-2026-MCA-01")
        self.assertEqual(fs_item["target_role"], "Full Stack Software Engineer")
        self.assertEqual(fs_item["answered_count"], 3)
        self.assertEqual(fs_item["technical_score"], 4.5)

        # Find Python Developer item
        py_item = next(h for h in history if h["session_code"] == "NXH-20261006-F48902")
        self.assertEqual(py_item["target_role"], "Python Developer")
        self.assertEqual(py_item["answered_count"], 0)
        self.assertEqual(py_item["skipped_count"], 3)
        self.assertIsNone(py_item["technical_score"])

    def test_F_partial_interview(self):
        """Test F: Interview with 1 answered and 2 skipped questions."""
        # Initialize
        res_init = self.client.post("/api/interview/init")
        s_code = res_init.get_json()["session_code"]

        # Upload dummy resume
        import io
        file_tuple = (io.BytesIO(b"Dummy candidate resume text with Python skills."), "resume.pdf")
        self.client.post("/api/interview/upload-resume", data={"session_code": s_code, "resume": file_tuple}, content_type="multipart/form-data")

        # Select role
        self.client.post("/api/interview/select-role", json={"session_code": s_code, "target_role": "Python Backend Developer"})

        # Start round
        res_start = self.client.post("/api/interview/start-round", json={"session_code": s_code})
        q1 = res_start.get_json()["first_question"]

        # Answer Question 1
        res_q1 = self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q1["id"],
            "transcript_text": "Python uses reference counting and garbage collection for memory management.",
            "status": "answered"
        })
        q2 = res_q1.get_json()["next_question"]

        # Skip Question 2
        res_q2 = self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q2["id"],
            "transcript_text": "",
            "status": "skipped"
        })
        q3 = res_q2.get_json()["next_question"]

        # Skip Question 3
        self.client.post("/api/interview/submit-answer", json={
            "session_code": s_code,
            "question_id": q3["id"],
            "transcript_text": "",
            "status": "skipped"
        })

        # Evaluate session
        res_eval = self.client.post("/api/interview/evaluate", json={"session_code": s_code})
        report = res_eval.get_json()["report"]

        self.assertEqual(report["total_questions"], 3)
        self.assertEqual(report["answered_count"], 1)
        self.assertEqual(report["skipped_count"], 2)
        self.assertIsNotNone(report["technical_score"])
        self.assertIsNotNone(report["limited_evidence_note"])

        q_evals = report["question_evaluations"]
        self.assertEqual(q_evals[0]["status"], "answered")
        self.assertEqual(q_evals[1]["status"], "skipped")
        self.assertEqual(q_evals[2]["status"], "skipped")

if __name__ == "__main__":
    unittest.main()
