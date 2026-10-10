"""
NextHire - End-to-End JARVIS Workflow Verification Test
Tests the complete 5-step onboarding lifecycle and strict validation:
1. Init Session (AWAITING_RESUME)
2. Strict Backend Rejection when selecting role without resume
3. Resume Upload (PyMuPDF / text extraction) -> AWAITING_ROLE
4. Target Role Selection -> Automated Analysis & Question Prep -> READY_FOR_ROUND
5. Continue -> "Let's Start!" -> First Question delivered
6. Cross-Session Isolation Verification (Session 1 vs Session 2)
"""
import unittest
import io
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app

class TestJarvisWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_complete_step_by_step_workflow(self):
        # ---------------------------------------------------------
        # STEP 0 / 1: Initialize Session
        # ---------------------------------------------------------
        res_init = self.client.post("/api/interview/init")
        self.assertEqual(res_init.status_code, 201)
        data_init = res_init.get_json()
        self.assertTrue(data_init["success"])
        session_code = data_init["session_code"]
        self.assertEqual(data_init["status"], "AWAITING_RESUME")
        self.assertIn("Welcome to NextHire. Please upload your resume to continue.", data_init["jarvis_voice_prompt"])

        # ---------------------------------------------------------
        # STRICT VALIDATION: Cannot select role without resume
        # ---------------------------------------------------------
        res_role_premature = self.client.post("/api/interview/select-role", json={
            "session_code": session_code,
            "target_role": "Python Developer"
        })
        self.assertEqual(res_role_premature.status_code, 400)
        self.assertIn("Resume", res_role_premature.get_json()["error"])

        # ---------------------------------------------------------
        # STRICT VALIDATION: Cannot start round without resume & role
        # ---------------------------------------------------------
        res_start_premature = self.client.post("/api/interview/start-round", json={
            "session_code": session_code
        })
        self.assertEqual(res_start_premature.status_code, 403)

        # ---------------------------------------------------------
        # STEP 1: Upload Resume
        # ---------------------------------------------------------
        sample_resume_content = (
            "John Doe - Senior Software Engineer\n"
            "Skills: Python, Flask, Django, MySQL, Docker, Git, REST API\n"
            "Experience in building scalable microservices and data pipelines."
        )
        fake_file = (io.BytesIO(sample_resume_content.encode("utf-8")), "resume.pdf")

        res_upload = self.client.post(
            "/api/interview/upload-resume",
            data={
                "session_code": session_code,
                "resume": fake_file
            },
            content_type="multipart/form-data"
        )
        self.assertEqual(res_upload.status_code, 200)
        data_upload = res_upload.get_json()
        self.assertTrue(data_upload["success"])
        self.assertEqual(data_upload["status"], "AWAITING_ROLE")
        self.assertEqual(data_upload["message"], "Resume uploaded successfully.")
        self.assertIn("Resume uploaded successfully.", data_upload["jarvis_voice_prompt"])
        self.assertIn("Python", data_upload["extracted_skills"])

        # ---------------------------------------------------------
        # STEP 2 & 3: Select Target Role -> Automated Analysis & Question Prep
        # ---------------------------------------------------------
        res_role = self.client.post("/api/interview/select-role", json={
            "session_code": session_code,
            "target_role": "Python Developer"
        })
        self.assertEqual(res_role.status_code, 200)
        data_role = res_role.get_json()
        self.assertTrue(data_role["success"])
        self.assertEqual(data_role["status"], "READY_FOR_ROUND")
        self.assertTrue(data_role["ready_for_round"])
        self.assertEqual(data_role["notification"], "Your interview is ready.")
        self.assertEqual(data_role["prompt_question"], "Are you ready for the JARVIS round?")
        self.assertEqual(data_role["action_button"], "Continue →")

        # ---------------------------------------------------------
        # STEP 4 & 5: Candidate Clicks Continue -> "Let's Start!" -> First Question
        # ---------------------------------------------------------
        res_round = self.client.post("/api/interview/start-round", json={
            "session_code": session_code
        })
        self.assertEqual(res_round.status_code, 200)
        data_round = res_round.get_json()
        self.assertTrue(data_round["success"])
        self.assertEqual(data_round["status"], "IN_PROGRESS")
        self.assertEqual(data_round["popup_message"], "Let's Start!")
        self.assertEqual(data_round["jarvis_voice_prompt"], "Let's start.")
        self.assertIsNotNone(data_round["first_question"])
        self.assertIn("Python", data_round["first_question"]["target_role"])

    def test_session_isolation(self):
        """
        Verify that Session 1 (Python Developer) and Session 2 (Java Developer)
        maintain completely isolated questions and target roles.
        """
        # Session 1: Python
        s1_init = self.client.post("/api/interview/init").get_json()["session_code"]
        f1 = (io.BytesIO(b"Python developer skills: Python, Flask"), "res1.pdf")
        self.client.post("/api/interview/upload-resume", data={"session_code": s1_init, "resume": f1}, content_type="multipart/form-data")
        self.client.post("/api/interview/select-role", json={"session_code": s1_init, "target_role": "Python Developer"})
        s1_round = self.client.post("/api/interview/start-round", json={"session_code": s1_init}).get_json()

        # Session 2: Java
        s2_init = self.client.post("/api/interview/init").get_json()["session_code"]
        f2 = (io.BytesIO(b"Java developer skills: Java, Spring Boot"), "res2.docx")
        self.client.post("/api/interview/upload-resume", data={"session_code": s2_init, "resume": f2}, content_type="multipart/form-data")
        self.client.post("/api/interview/select-role", json={"session_code": s2_init, "target_role": "Java Developer"})
        s2_round = self.client.post("/api/interview/start-round", json={"session_code": s2_init}).get_json()

        # Assert isolation
        self.assertNotEqual(s1_init, s2_init)
        self.assertEqual(s1_round["first_question"]["target_role"], "Python Developer")
        self.assertEqual(s2_round["first_question"]["target_role"], "Java Developer")
        self.assertNotEqual(s1_round["first_question"]["question_text"], s2_round["first_question"]["question_text"])

if __name__ == "__main__":
    unittest.main()
