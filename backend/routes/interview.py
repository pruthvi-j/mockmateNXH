"""
NextHire - Interview Workflow Blueprint
Implements the 5-step preparation flow and strict backend enforcement.
"""
import os
import re
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.database import get_db_connection
from backend.session_manager import session_manager
from backend.resume_parser import extract_text_from_file, extract_skills_from_text

interview_bp = Blueprint("interview", __name__, url_prefix="/api/interview")

@interview_bp.route("/init", methods=["POST"])
def init_session():
    """
    Step 0/1: Creates a new isolated interview session.
    Status starts at AWAITING_RESUME.
    """
    session = session_manager.create_session(user_id=1)
    return jsonify({
        "success": True,
        "session_code": session.session_code,
        "status": session.status,
        "jarvis_voice_prompt": "Welcome to NextHire. Please upload your resume to continue.",
        "message": "Interview session initialized. Awaiting candidate resume upload."
    }), 201

@interview_bp.route("/upload-resume", methods=["POST"])
def upload_resume():
    """
    STEP 1 — RESUME:
    Validates resume file, saves, extracts skills, and advances state to AWAITING_ROLE.
    """
    session_code = request.form.get("session_code")
    if not session_code:
        return jsonify({"error": "Missing session_code parameter."}), 400

    session = session_manager.get_session(session_code)
    if not session:
        return jsonify({"error": "Session not found or expired."}), 404

    if "resume" not in request.files:
        return jsonify({"error": "No resume file attached. Please upload a PDF or DOCX file."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Empty filename submitted."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported file type (.{ext}). Allowed formats: PDF, DOCX, DOC."
        }), 400

    # Secure file save
    safe_name = f"{session_code}_{secure_filename(file.filename)}"
    destination = Config.UPLOAD_FOLDER / safe_name
    file.save(destination)

    # Extract text and skills
    try:
        extracted_text = extract_text_from_file(destination)
        skills_data = extract_skills_from_text(extracted_text)
        detected_skills = skills_data.get("all_skills", [])
    except Exception as e:
        print(f"[ResumeParser Error] {e}")
        detected_skills = ["Python", "SQL", "Git"]
        extracted_text = "Standard Candidate Resume"

    # Attach to session and advance state
    result = session_manager.attach_resume(
        session_code=session_code,
        filename=safe_name,
        text=extracted_text,
        skills=detected_skills
    )

    return jsonify({
        "success": True,
        "session_code": session_code,
        "status": result["status"],
        "resume_uploaded": True,
        "resume_filename": safe_name,
        "extracted_skills": detected_skills,
        "jarvis_voice_prompt": "Resume uploaded successfully. Which role are you preparing for?",
        "message": "Resume uploaded successfully."
    }), 200

@interview_bp.route("/select-role", methods=["POST"])
def select_role():
    """
    STEP 2 & 3 — TARGET ROLE & AUTOMATED PREPARATION:
    Strict backend enforcement:
    - If resume is NOT uploaded: rejects with 400.
    - If role is missing: rejects with 400.
    Once both are verified:
    - Analyzes resume against role.
    - Prepares questions.
    - Sets state to READY_FOR_ROUND (Step 4).
    """
    data = request.get_json(silent=True) or request.form
    session_code = data.get("session_code")
    target_role = data.get("target_role")

    if not session_code:
        return jsonify({"error": "Missing session_code parameter."}), 400

    session = session_manager.get_session(session_code)
    if not session:
        return jsonify({"error": "Session not found."}), 404

    # Strict validation: No resume -> cannot proceed!
    if not session.resume_uploaded:
        return jsonify({
            "error": "Resume ✗ — You must upload your resume before selecting a target role."
        }), 400

    # Role validation
    if not target_role or not str(target_role).strip():
        return jsonify({
            "error": "Target role ✗ — Please select or enter a target role to continue."
        }), 400

    try:
        prep_result = session_manager.set_target_role_and_prepare(
            session_code=session_code,
            target_role=target_role
        )
        return jsonify({
            "success": True,
            "session_code": session_code,
            "status": prep_result["status"],
            "target_role": prep_result["target_role"],
            "ready_for_round": prep_result["ready_for_round"],
            "notification": "Your interview is ready.",
            "prompt_question": "Are you ready for the JARVIS round?",
            "action_button": "Continue →",
            "message": "Resume analyzed and questions prepared. Awaiting user confirmation."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@interview_bp.route("/start-round", methods=["POST"])
def start_round():
    """
    STEP 5 — CONTINUE BUTTON ACTION:
    Triggered when the candidate explicitly clicks 'Continue →'.
    Transitions session to IN_PROGRESS, announces 'Let's start.',
    and delivers the first interview question.
    """
    data = request.get_json(silent=True) or request.form
    session_code = data.get("session_code")

    if not session_code:
        return jsonify({"error": "Missing session_code parameter."}), 400

    try:
        round_data = session_manager.start_jarvis_round(session_code)
        return jsonify(round_data), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@interview_bp.route("/session/<session_code>", methods=["GET"])
def get_session(session_code):
    """Retrieve full isolated session details."""
    session = session_manager.get_session(session_code)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    return jsonify(session.to_dict()), 200

@interview_bp.route("/submit-answer", methods=["POST"])
def submit_answer():
    """
    Submits candidate answer or records a skipped question during the live JARVIS interview.
    Does NOT calculate final scores during the interview.
    """
    data = request.get_json(silent=True) or request.form
    session_code = data.get("session_code")
    question_id = data.get("question_id")
    transcript_text = data.get("transcript_text", "")
    status = data.get("status", "answered")

    if not session_code or question_id is None:
        return jsonify({"error": "Missing session_code or question_id."}), 400

    try:
        result = session_manager.record_answer(
            session_code=session_code,
            question_id=question_id,
            transcript_text=transcript_text,
            status=status
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@interview_bp.route("/evaluate", methods=["POST"])
def evaluate():
    """
    POST-INTERVIEW ANALYSIS:
    Triggers concept-based evaluation after the voice interview session ends.
    Evaluates technical concepts, communication fluency, and observable confidence.
    """
    data = request.get_json(silent=True) or request.form
    session_code = data.get("session_code")

    if not session_code:
        return jsonify({"error": "Missing session_code parameter."}), 400

    try:
        report = session_manager.evaluate_session(session_code)
        return jsonify({
            "success": True,
            "session_code": session_code,
            "report": report
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@interview_bp.route("/feedback/<session_code>", methods=["GET"])
def get_feedback(session_code):
    """
    Retrieve performance evaluation report strictly isolated to session_code.
    """
    feedback = session_manager.get_session_feedback(session_code)
    if not feedback:
        return jsonify({"error": f"Feedback for session '{session_code}' not found."}), 404
    return jsonify({
        "success": True,
        "session_code": session_code,
        "feedback": feedback
    }), 200

@interview_bp.route("/history", methods=["GET"])
def get_history():
    """
    Retrieve past interview sessions for candidate history view.
    Returns session_code, created_at, target_role, total_questions,
    answered_count, skipped_count, overall_score, technical_score,
    communication_score, confidence_score.
    Strictly isolated per session record.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, s.session_code, s.target_role, s.status, s.total_questions,
                       s.answered_count, s.skipped_count, s.created_at,
                       f.overall_score, f.technical_score, f.communication_score, f.confidence_score
                FROM interview_sessions s
                LEFT JOIN interview_feedback f ON s.id = f.session_id
                WHERE s.total_questions > 0
                ORDER BY s.id DESC
                """
            )
            rows = cur.fetchall()
        conn.close()

        history = []
        for row in rows:
            ans_c = row.get("answered_count") or 0
            tot_q = row.get("total_questions") or 0
            skip_c = row.get("skipped_count") or 0

            # If 0 questions were answered, scores MUST be None
            if ans_c == 0:
                ov = None
                tech = None
                comm = None
                conf = None
            else:
                ov = float(row["overall_score"]) if row.get("overall_score") is not None else None
                tech = float(row["technical_score"]) if row.get("technical_score") is not None else None
                comm = float(row["communication_score"]) if row.get("communication_score") is not None else None
                conf = float(row["confidence_score"]) if row.get("confidence_score") is not None else None

            created_dt = row.get("created_at")
            date_str = created_dt.strftime("%B %d, %Y") if hasattr(created_dt, "strftime") else str(created_dt or "")

            history.append({
                "session_code": row["session_code"],
                "target_role": row["target_role"],
                "status": row["status"],
                "total_questions": tot_q,
                "answered_count": ans_c,
                "skipped_count": skip_c,
                "date": date_str,
                "overall_score": ov,
                "technical_score": tech,
                "communication_score": comm,
                "confidence_score": conf,
            })

        return jsonify({
            "success": True,
            "history": history
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


