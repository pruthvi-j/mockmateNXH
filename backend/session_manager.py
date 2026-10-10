"""
NextHire - Session Management & Isolation Engine
Enforces the 5-step interview preparation workflow and MySQL persistence.
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from backend.database import get_db_connection
from backend.question_bank import prepare_interview_questions

class InterviewSession:
    def __init__(self, session_code: str, user_id: int = 1):
        self.session_code = session_code
        self.user_id = user_id
        self.status = "AWAITING_RESUME"  # Step 1
        self.resume_uploaded = False
        self.resume_filename = None
        self.resume_text = ""
        self.extracted_skills = []
        self.target_role = None          # Step 2
        self.questions = []              # Step 3
        self.current_question_index = 0
        self.ready_for_round = False     # Step 4
        self.round_started = False       # Step 5
        self.created_at = datetime.now()
        self.answers = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_code": self.session_code,
            "status": self.status,
            "resume_uploaded": self.resume_uploaded,
            "resume_filename": self.resume_filename,
            "extracted_skills": self.extracted_skills,
            "target_role": self.target_role,
            "total_questions": len(self.questions),
            "current_question_index": self.current_question_index,
            "ready_for_round": self.ready_for_round,
            "round_started": self.round_started,
            "created_at": self.created_at.isoformat()
        }

class SessionManager:
    """Singleton session registry managing active candidate interview sessions."""
    def __init__(self):
        self._sessions: Dict[str, InterviewSession] = {}

    def create_session(self, user_id: int = 1) -> InterviewSession:
        """Create a new isolated interview session."""
        code = f"NXH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        session = InterviewSession(session_code=code, user_id=user_id)
        self._sessions[code] = session

        # Persist to MySQL
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO interview_sessions (session_code, user_id, target_role, status, total_questions)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (code, user_id, "Pending Selection", "in_progress", 0)
                )
            conn.close()
        except Exception as e:
            print(f"[SessionManager] DB Sync notice: {e}")

        return session

    def get_session(self, session_code: str) -> Optional[InterviewSession]:
        return self._sessions.get(session_code)

    def attach_resume(self, session_code: str, filename: str, text: str, skills: list) -> Dict[str, Any]:
        """
        STEP 1 — RESUME:
        Validates and marks resume as uploaded for the session.
        Transitions status from AWAITING_RESUME to AWAITING_ROLE.
        """
        session = self.get_session(session_code)
        if not session:
            raise ValueError("Invalid session code.")

        session.resume_uploaded = True
        session.resume_filename = filename
        session.resume_text = text
        session.extracted_skills = skills
        session.status = "AWAITING_ROLE"  # Ready for Step 2

        # Sync to MySQL resumes table
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO resumes (user_id, filename, file_path, extracted_text, extracted_skills)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session.user_id, filename, f"uploads/{filename}", text[:2000], json.dumps(skills))
                )
            conn.close()
        except Exception as e:
            print(f"[SessionManager] Resume DB Sync notice: {e}")

        return {
            "success": True,
            "session_code": session.session_code,
            "status": session.status,
            "resume_filename": filename,
            "skills": skills,
            "message": "Resume uploaded successfully."
        }

    def set_target_role_and_prepare(self, session_code: str, target_role: str) -> Dict[str, Any]:
        """
        STEP 2 & 3 — TARGET ROLE + ANALYSIS:
        Strict validation: Cannot select role if resume has not been uploaded.
        Once both are completed, automatically prepares questions and marks READY_FOR_ROUND.
        """
        session = self.get_session(session_code)
        if not session:
            raise ValueError("Invalid session code.")

        # Strict validation: Resume must be uploaded first!
        if not session.resume_uploaded:
            raise PermissionError("Resume has not been uploaded. Please upload your resume first.")

        if not target_role or not target_role.strip():
            raise ValueError("Please provide a valid target role.")

        session.target_role = target_role.strip()
        session.status = "ANALYZING"

        # Step 3: Automated Question Preparation
        prepared_questions = prepare_interview_questions(
            target_role=session.target_role,
            extracted_skills=session.extracted_skills,
            count=3
        )
        session.questions = prepared_questions
        session.status = "READY_FOR_ROUND"  # Step 4: Ready for Continue button
        session.ready_for_round = True

        # Sync to MySQL interview_sessions table
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE interview_sessions
                    SET target_role = %s, total_questions = %s
                    WHERE session_code = %s
                    """,
                    (session.target_role, len(prepared_questions), session_code)
                )
            conn.close()
        except Exception as e:
            print(f"[SessionManager] Question Prep DB Sync notice: {e}")

        return {
            "success": True,
            "session_code": session.session_code,
            "status": session.status,
            "target_role": session.target_role,
            "questions_prepared": len(prepared_questions),
            "ready_for_round": session.ready_for_round,
            "message": "Your interview is ready. Are you ready for the JARVIS round?"
        }

    def start_jarvis_round(self, session_code: str) -> Dict[str, Any]:
        """
        STEP 5 — CONTINUE BUTTON TRIGGER:
        User explicitly clicks 'Continue ->'.
        Transitions session to IN_PROGRESS and delivers first question.
        """
        session = self.get_session(session_code)
        if not session:
            raise ValueError("Invalid session code.")

        if not session.resume_uploaded:
            raise PermissionError("Cannot start interview: Resume missing.")

        if not session.target_role:
            raise PermissionError("Cannot start interview: Target role not selected.")

        if not session.ready_for_round:
            raise PermissionError("Interview preparation is not complete.")

        session.round_started = True
        session.status = "IN_PROGRESS"
        session.current_question_index = 0
        session.answers = []

        first_question = session.questions[0] if session.questions else None

        return {
            "success": True,
            "session_code": session.session_code,
            "status": session.status,
            "round_started": True,
            "popup_message": "Let's Start!",
            "jarvis_voice_prompt": "Let's start.",
            "current_question_index": 0,
            "total_questions": len(session.questions),
            "first_question": {
                "id": first_question["id"] if first_question else None,
                "question_code": first_question["question_code"] if first_question else None,
                "target_role": session.target_role,
                "category": first_question["category"] if first_question else "Technical",
                "difficulty": first_question["difficulty"] if first_question else "Intermediate",
                "question_text": first_question["question_text"] if first_question else "",
                "key_concepts": first_question["key_concepts"] if first_question else []
            } if first_question else None
        }

    def record_answer(self, session_code: str, question_id: Any, transcript_text: str = "", status: str = "answered") -> Dict[str, Any]:
        """
        Record a candidate answer or skipped question during the live JARVIS interview.
        Does NOT score the answer during the interview.
        """
        session = self.get_session(session_code)
        if not session:
            raise ValueError("Session not found.")

        # Match question
        q_obj = None
        for q in session.questions:
            if str(q.get("id")) == str(question_id) or str(q.get("question_code")) == str(question_id):
                q_obj = q
                break

        answer_record = {
            "question_id": question_id,
            "question_code": q_obj["question_code"] if q_obj else str(question_id),
            "transcript_text": transcript_text.strip() if status != "skipped" else "",
            "status": "skipped" if status == "skipped" else "answered",
            "recorded_at": datetime.now().isoformat()
        }
        session.answers.append(answer_record)

        # Advance question index
        session.current_question_index += 1
        is_completed = session.current_question_index >= len(session.questions)

        # Persist answer to MySQL
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Find DB session id
                cur.execute("SELECT id FROM interview_sessions WHERE session_code = %s", (session_code,))
                db_s = cur.fetchone()
                if db_s:
                    db_sid = db_s["id"] if isinstance(db_s, dict) else db_s[0]
                    # Map numeric qid
                    numeric_qid = q_obj.get("id", 1) if q_obj else 1
                    cur.execute(
                        """
                        INSERT INTO user_answers (session_id, question_id, transcript_text)
                        VALUES (%s, %s, %s)
                        """,
                        (db_sid, numeric_qid, answer_record["transcript_text"] if status != "skipped" else "[SKIPPED]")
                    )
            conn.close()
        except Exception as e:
            print(f"[SessionManager] Answer DB sync notice: {e}")

        next_q = None
        if not is_completed and session.current_question_index < len(session.questions):
            next_raw = session.questions[session.current_question_index]
            next_q = {
                "id": next_raw["id"],
                "question_code": next_raw["question_code"],
                "target_role": session.target_role,
                "category": next_raw.get("category", "Technical"),
                "difficulty": next_raw.get("difficulty", "Intermediate"),
                "question_text": next_raw["question_text"],
                "key_concepts": next_raw.get("key_concepts", [])
            }

        return {
            "success": True,
            "session_code": session_code,
            "recorded_status": answer_record["status"],
            "current_question_index": session.current_question_index,
            "total_questions": len(session.questions),
            "is_completed": is_completed,
            "next_question": next_q
        }

    def evaluate_session(self, session_code: str) -> Dict[str, Any]:
        """
        POST-INTERVIEW ANALYSIS:
        Evaluates the complete session after the voice interview ends.
        Computes concept-based technical quality, session communication, and observable confidence.
        Guarantees strict isolation by session_code.
        """
        from backend.evaluation_engine import evaluate_entire_session

        session = self.get_session(session_code)
        if not session:
            raise ValueError(f"Session '{session_code}' not found.")

        # Build complete payload for evaluation
        eval_payload = {
            "session_code": session.session_code,
            "target_role": session.target_role,
            "questions": session.questions,
            "answers": session.answers,
            "resume_skills": session.extracted_skills or []
        }

        eval_result = evaluate_entire_session(eval_payload)
        session.status = "COMPLETED"
        session.feedback = eval_result

        # Persist feedback to MySQL
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM interview_sessions WHERE session_code = %s", (session_code,))
                db_s = cur.fetchone()
                if db_s:
                    db_sid = db_s["id"] if isinstance(db_s, dict) else db_s[0]
                    # Update session status
                    cur.execute(
                        """
                        UPDATE interview_sessions
                        SET status = 'completed',
                            answered_count = %s,
                            skipped_count = %s,
                            completed_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (eval_result["answered_count"], eval_result["skipped_count"], db_sid)
                    )
                    # Insert or replace into interview_feedback
                    cur.execute(
                        """
                        INSERT INTO interview_feedback (
                            session_id, overall_score, technical_score, communication_score,
                            confidence_score, strengths, weaknesses, recommendations, summary_text
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            overall_score = VALUES(overall_score),
                            technical_score = VALUES(technical_score),
                            communication_score = VALUES(communication_score),
                            confidence_score = VALUES(confidence_score),
                            strengths = VALUES(strengths),
                            weaknesses = VALUES(weaknesses),
                            recommendations = VALUES(recommendations),
                            summary_text = VALUES(summary_text)
                        """,
                        (
                            db_sid,
                            eval_result["overall_score"],
                            eval_result["technical_score"],
                            eval_result["communication_score"],
                            eval_result["confidence_score"],
                            json.dumps(eval_result["strengths"]),
                            json.dumps(eval_result["weaknesses"]),
                            json.dumps(eval_result["recommendations"]),
                            f"Evaluated session for {session.target_role} with {eval_result['answered_percentage']}% completion."
                        )
                    )
            conn.close()
        except Exception as e:
            print(f"[SessionManager] Feedback DB sync notice: {e}")

        return eval_result

    def get_session_feedback(self, session_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve evaluation feedback strictly isolated to the specified session_code.
        Never returns data belonging to another session.
        """
        session = self.get_session(session_code)
        if session and hasattr(session, "feedback") and session.feedback:
            return session.feedback

        # If not in memory, query MySQL strictly for this session_code
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.id, s.session_code, s.target_role, s.total_questions, s.answered_count, s.skipped_count,
                           f.overall_score, f.technical_score, f.communication_score, f.confidence_score,
                           f.strengths, f.weaknesses, f.recommendations, f.summary_text
                    FROM interview_sessions s
                    LEFT JOIN interview_feedback f ON s.id = f.session_id
                    WHERE s.session_code = %s
                    """,
                    (session_code,)
                )
                row = cur.fetchone()
                if row:
                    total_q = row["total_questions"] or 0
                    ans_c = row["answered_count"] or 0
                    skip_c = row["skipped_count"] or 0
                    pct = round((ans_c / max(total_q, 1)) * 100, 1) if total_q else 0

                    if ans_c == 0:
                        ov_score = None
                        tech_score = None
                        comm_score = None
                        conf_score = None
                        lim_note = "No questions were answered during this interview session. Technical, communication, and confidence scores cannot be reliably evaluated."
                    else:
                        ov_score = float(row["overall_score"]) if row.get("overall_score") is not None else None
                        tech_score = float(row["technical_score"]) if row.get("technical_score") is not None else None
                        comm_score = float(row["communication_score"]) if row.get("communication_score") is not None else None
                        conf_score = float(row["confidence_score"]) if row.get("confidence_score") is not None else None
                        lim_note = (
                            f"Technical performance is based on {ans_c} answered question(s) out of {total_q} "
                            f"({pct}% coverage), so the result represents limited interview evidence."
                        ) if ans_c < total_q else None

                    # Fetch user answers to populate question evaluations
                    from backend.evaluation_engine import evaluate_one_question
                    from backend.question_bank import QUESTION_STORE

                    cur.execute(
                        """
                        SELECT ua.question_id, ua.transcript_text, qb.question_code, qb.question_text, qb.category, qb.difficulty
                        FROM user_answers ua
                        LEFT JOIN question_bank qb ON ua.question_id = qb.id
                        WHERE ua.session_id = %s
                        """,
                        (row["id"],)
                    )
                    user_ans_rows = cur.fetchall() or []

                    question_evaluations = []
                    for idx, u_ans in enumerate(user_ans_rows):
                        q_code = u_ans.get("question_code") or f"Q{idx+1}"
                        q_text = u_ans.get("question_text") or "Interview Question"
                        t_text = u_ans.get("transcript_text") or ""
                        is_skp = (t_text == "[SKIPPED]" or not t_text.strip())

                        # Match with question store for expected concepts & reference answer
                        q_store_item = None
                        for q_item in QUESTION_STORE:
                            if q_item.get("question_code") == q_code or str(q_item.get("id")) == str(u_ans.get("question_id")):
                                q_store_item = q_item
                                break

                        expected_conc = q_store_item.get("key_concepts", []) if q_store_item else []
                        ref_ans = q_store_item.get("reference_answer", "") if q_store_item else ""
                        category = u_ans.get("category") or (q_store_item.get("category") if q_store_item else "Technical")
                        difficulty = u_ans.get("difficulty") or (q_store_item.get("difficulty") if q_store_item else "Intermediate")
                        if q_store_item and q_store_item.get("question_text"):
                            q_text = q_store_item["question_text"]

                        if is_skp:
                            question_evaluations.append({
                                "question_id": str(u_ans.get("question_id") or idx+1),
                                "question_code": q_code,
                                "question_text": q_text,
                                "category": category,
                                "difficulty": difficulty,
                                "status": "skipped",
                                "user_answer": "[Question skipped - no answer recorded]",
                                "concepts_expected": expected_conc,
                                "concepts_identified": [],
                                "concepts_missing": expected_conc,
                                "concept_match": "Skipped",
                                "concept_match_label": "Skipped",
                                "technical_score": None,
                                "dimensions": {},
                                "feedback": "This question was skipped. No technical evaluation was performed."
                            })
                        else:
                            eval_res = evaluate_one_question(
                                question_text=q_text,
                                expected_concepts=expected_conc,
                                reference_answer=ref_ans,
                                user_answer=t_text,
                                category=category
                            )
                            question_evaluations.append({
                                "question_id": str(u_ans.get("question_id") or idx+1),
                                "question_code": q_code,
                                "question_text": q_text,
                                "category": category,
                                "difficulty": difficulty,
                                "status": "answered",
                                "user_answer": t_text,
                                "concepts_expected": eval_res["concepts_expected"],
                                "concepts_identified": eval_res["concepts_identified"],
                                "concepts_missing": eval_res["concepts_missing"],
                                "concept_match": eval_res["concept_match_label"],
                                "concept_match_label": eval_res["concept_match_label"],
                                "technical_score": eval_res["score"],
                                "dimensions": eval_res.get("dimensions", {}),
                                "feedback": eval_res["feedback"]
                            })

                    return {
                        "session_code": row["session_code"],
                        "target_role": row["target_role"],
                        "total_questions": total_q,
                        "answered_count": ans_c,
                        "skipped_count": skip_c,
                        "answered_display": f"{ans_c}/{total_q}",
                        "answered_percentage": pct,
                        "overall_score": ov_score,
                        "technical_score": tech_score,
                        "communication_score": comm_score,
                        "confidence_score": conf_score,
                        "limited_evidence_note": lim_note,
                        "strengths": json.loads(row["strengths"]) if isinstance(row.get("strengths"), str) else (row.get("strengths") or []),
                        "weaknesses": json.loads(row["weaknesses"]) if isinstance(row.get("weaknesses"), str) else (row.get("weaknesses") or []),
                        "recommendations": json.loads(row["recommendations"]) if isinstance(row.get("recommendations"), str) else (row.get("recommendations") or []),
                        "question_evaluations": question_evaluations
                    }
            conn.close()
        except Exception as e:
            print(f"[SessionManager] DB Feedback lookup notice: {e}")

        # If session exists but was not yet evaluated, evaluate now
        if session and session.questions:
            return self.evaluate_session(session_code)

        return None

session_manager = SessionManager()

