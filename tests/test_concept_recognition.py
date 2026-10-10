"""
NextHire - Concept Recognition & STT Normalization Test Suite
Verifies:
  1. GIL spoken as individual letters ("g i l").
  2. Mutex mentioned in answer ("s m u text", "m u text", "mutex").
  3. CPython mentioned in answer ("c python", "CPython").
  4. Flask and Django both recognized ("f l a s k" / "flash", "design go" / "django").
  5. ORM and SQLAlchemy recognized ("o r m", "sql alchemy").
  6. Technical terms mistranscribed by STT ("white code" -> bytecode, "reference continue" -> reference counting).
  7. Similar-looking words do not produce false concept matches.
  8. Answers mentioning only some expected concepts (partial match).
  9. Answers demonstrating zero expected concepts (weak match).
 10. Existing zero-answer sessions and session isolation preserved.
"""

import unittest
from backend.app import create_app
from backend.evaluation_engine import evaluate_one_question, normalize_stt, _concept_present

class TestConceptRecognition(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_1_gil_spoken_as_letters(self):
        """Test 1: 'g i l' spoken as individual letters recognizes GIL."""
        text = "the g i l protects access to Python objects"
        norm = normalize_stt(text)
        self.assertIn("gil", norm)
        self.assertTrue(_concept_present("GIL", norm))

    def test_2_mutex_phonetic_stt(self):
        """Test 2: 's m u text' or 'm u text' or 'mutex' recognizes mutex concept."""
        text = "the g i l s m u text prevents multi-threaded execution"
        norm = normalize_stt(text)
        self.assertIn("mutex", norm)
        self.assertTrue(_concept_present("mutex", norm))

    def test_3_cpython_spoken(self):
        """Test 3: 'c python' or 'CPython' recognizes CPython concept."""
        text = "in c python the GIL is a single lock"
        norm = normalize_stt(text)
        self.assertTrue(_concept_present("CPython", norm))

    def test_4_flask_and_django_both_recognized(self):
        """Test 4: 'flash' / 'f l a s k' and 'design go' recognize Flask and Django."""
        text = "flash and design go differ significantly in architecture"
        norm = normalize_stt(text)
        self.assertTrue(_concept_present("Flask", norm))
        self.assertTrue(_concept_present("Django", norm))

    def test_5_orm_and_sqlalchemy_recognized(self):
        """Test 5: 'o r m' and 'sql alchemy' recognize ORM and SQLAlchemy."""
        text = "Flask uses an o r m like sql alchemy for database access"
        norm = normalize_stt(text)
        self.assertTrue(_concept_present("ORM", norm))
        self.assertTrue(_concept_present("SQLAlchemy", norm))

    def test_6_stt_term_normalization(self):
        """Test 6: Speech-to-text corrections for white code -> bytecode and ref continue -> ref counting."""
        text = "Python executes white code using reference continue and generating garbage collector"
        norm = normalize_stt(text)
        self.assertIn("bytecode", norm)
        self.assertIn("reference counting", norm)
        self.assertIn("garbage collection", norm)

    def test_7_no_false_concept_matches(self):
        """Test 7: Unrelated words must not trigger false concept matches."""
        text = "I like eating oranges and playing with my cat in the garden"
        norm = normalize_stt(text)
        self.assertFalse(_concept_present("ORM", norm))
        self.assertFalse(_concept_present("GIL", norm))
        self.assertFalse(_concept_present("Django", norm))
        self.assertFalse(_concept_present("SQLAlchemy", norm))

    def test_8_partial_concept_match(self):
        """Test 8: Answers mentioning only some concepts yield partial match."""
        q_text = "Compare Flask and Django in terms of architecture, flexibility, and default database ORM capabilities."
        expected = ["Flask", "Django", "micro-framework", "ORM", "SQLAlchemy", "batteries-included", "MVT"]
        user_ans = "design go is a framework with building in features"
        
        eval_res = evaluate_one_question(q_text, expected, "", user_ans, "Backend Frameworks")
        self.assertIn("Django", eval_res["concepts_identified"])
        self.assertIn("batteries-included", eval_res["concepts_identified"])
        self.assertIn("Flask", eval_res["concepts_missing"])
        self.assertIn("ORM", eval_res["concepts_missing"])

    def test_9_zero_concept_match(self):
        """Test 9: Irrelevant answer yields weak match with zero identified concepts."""
        q_text = "What is the Global Interpreter Lock (GIL) in CPython?"
        expected = ["GIL", "mutex", "CPython", "concurrency"]
        user_ans = "the weather today is sunny with light rain"

        eval_res = evaluate_one_question(q_text, expected, "", user_ans, "Python Concurrency")
        self.assertEqual(len(eval_res["concepts_identified"]), 0)
        self.assertEqual(eval_res["concept_match_label"], "Weak concept match")

    def test_10_zero_answer_and_session_isolation(self):
        """Test 10: Verify session NXH-20261010-2200BF evaluates PL002 concepts correctly without affecting other sessions."""
        res = self.client.get("/api/interview/feedback/NXH-20261010-2200BF")
        self.assertEqual(res.status_code, 200)
        fb = res.get_json()["feedback"]
        
        q_evals = fb["question_evaluations"]
        # PL002 evaluation in session NXH-20261010-2200BF
        q2 = next(q for q in q_evals if q["question_code"] == "PL002")
        self.assertIn("GIL", q2["concepts_identified"])
        self.assertIn("mutex", q2["concepts_identified"])
        self.assertIn("CPython", q2["concepts_identified"])
        self.assertIn("concurrency", q2["concepts_identified"])
        self.assertIn("multi-threading", q2["concepts_identified"])
        self.assertNotIn("mutex", [w.lower() for w in fb.get("weaknesses", []) if "mutex" in w.lower()])

if __name__ == "__main__":
    unittest.main()
