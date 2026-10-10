"""
NextHire - Concept-Based Evaluation Engine v2
============================================
Core principles enforced by this module:

  1. ANSWER QUALITY != ANSWER COVERAGE
       - Technical Precision = quality of answered questions only
       - Answer Coverage     = answered / total questions
       - Skipped questions are NEVER treated as wrong answers

  2. EVIDENCE-BASED SCORING
       - Every score comes from the actual user answer
       - No score is fabricated to fill a UI field
       - Limited sample sizes are explicitly acknowledged

  3. SPEECH-TO-TEXT NORMALIZATION
       - Common STT transcription errors are resolved using
         surrounding context before any evaluation begins

  4. SEMANTIC CONCEPT MATCHING
       - Synonym / paraphrase expansion table
       - Partial credit for demonstrated understanding

  5. ROLE + RESUME AWARE RECOMMENDATIONS
       - Recommendations flow strictly from:
           question -> expected concepts -> user concepts -> missing concepts -> role
       - No unrelated topics are recommended
"""

import re
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# STT NORMALIZATION DICTIONARY
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# STT NORMALIZATION DICTIONARY
# ---------------------------------------------------------------------------
STT_CORRECTIONS: List[tuple] = [
    # Spoken letter sequences & acronyms
    (r"\bg\s+i\s+l\b", "gil"),
    (r"\bgill?\b", "gil"),
    (r"\bg\.i\.l\.?\b", "gil"),
    (r"\bg\s*i\s*l\s*s\b", "gil"),
    
    # Mutex phonetic/STT mishearings
    (r"\b(?:s\s*)?m\s*u\s*text\b", "mutex"),
    (r"\bmu\s*text\b", "mutex"),
    (r"\bmyu\s*tex\b", "mutex"),
    (r"\bmutual\s+exclusion\b", "mutex"),
    
    # CPython / Python
    (r"\bc\s+python\b", "cpython"),
    (r"\bc-python\b", "cpython"),
    (r"\bsee\s+python\b", "cpython"),
    
    # Frameworks
    (r"\bf\s+l\s+a\s+s\s+k\b", "flask"),
    (r"\bflash\b", "flask"),
    (r"\bflasks\b", "flask"),
    (r"\bd\s+j\s+a\s+n\s+g\s+o\b", "django"),
    (r"\bdesign\s*go\b", "django"),
    (r"\bdj[ae]ngo\b", "django"),
    (r"\bjan\s*go\b", "django"),
    
    # ORM & DB
    (r"\bo\s+r\s+m\b", "orm"),
    (r"\boram\b", "orm"),
    (r"\bo\.r\.m\b", "orm"),
    (r"\bsql\s+alchemy\b", "sqlalchemy"),
    (r"\bsql\s*alkemi\b", "sqlalchemy"),
    (r"\bsqla\b", "sqlalchemy"),
    (r"\bno\s+sql\b", "nosql"),
    (r"\bmy\s+sql\b", "mysql"),
    
    # Architecture & Design
    (r"\bm\s+v\s+t\b", "mvt"),
    (r"\bm\s+t\s+v\b", "mvt"),
    (r"\bm\.v\.t\.?\b", "mvt"),
    (r"\bm\.t\.v\.?\b", "mvt"),
    (r"\bbuilding\s+in\b", "built-in"),
    
    # Concurrency & Execution
    (r"\bmulti\s+thread(?:ing)?\b", "multi-threading"),
    (r"\bmultiple\s+native\s+threads?\b", "multi-threading"),
    (r"\bnative\s+threads?\b", "multi-threading"),
    (r"\bcpu\s+bound\b", "cpu-bound"),
    (r"\bwhite\s+code\b", "bytecode"),
    (r"\bbyte\s+code\b", "bytecode"),
    (r"\bref(?:erence)?\s+continue\b", "reference counting"),
    (r"\bref(?:erence)?\s+count\w*\b", "reference counting"),
    (r"\bgenerat\w*\s+garbage\s+collect\w*\b", "garbage collection"),
    (r"\bgar\w*\s+collect\w*\b", "garbage collection"),
    (r"\bci\s*/?\s*cd\b", "ci/cd"),
    (r"\bj\.w\.t\.?\b", "jwt"),
    (r"\bj\s+w\s+t\b", "jwt"),
    (r"\bres\s*ful\b", "restful"),
    (r"\bpyth?on\b", "python"),
]

# ---------------------------------------------------------------------------
# CONCEPT SYNONYM / PARAPHRASE MAP
# ---------------------------------------------------------------------------
CONCEPT_SYNONYMS: Dict[str, List[str]] = {
    "flask":             ["flask", "f l a s k", "micro framework", "micro-framework", "lightweight framework", "minimalist framework"],
    "django":            ["django", "d j a n g o", "design go", "full framework", "full-stack framework"],
    "micro-framework":   ["micro framework", "micro-framework", "minimalist", "lightweight", "minimal", "small framework"],
    "orm":               ["orm", "o r m", "object relational", "object-relational", "database abstraction", "db abstraction"],
    "sqlalchemy":        ["sqlalchemy", "sql alchemy", "sqla", "alchemy"],
    "batteries-included":["batteries included", "batteries-included", "built-in features", "built in features", "built-in dashboard", "building in dashboard", "bundled", "out of the box", "opinionated"],
    "mvt":               ["mvt", "m.v.t", "m.t.v", "model view template", "model-view-template"],
    "flexibility":       ["flexibility", "flexible", "freedom", "freedom of choice", "no constraints", "customizable"],
    "architecture":      ["architecture", "structure", "design", "pattern", "organized", "layered"],
    "memory management": ["memory management", "manages memory", "memory allocation", "heap management", "memory reclaim", "reclaim memory"],
    "garbage collection":["garbage collection", "garbage collector", "gc", "generational garbage collection", "cyclic collector", "automatic memory", "generation"],
    "reference counting":["reference counting", "ref count", "reference count", "ref-count", "count references", "reference continue"],
    "gil":               ["gil", "g i l", "global interpreter lock", "interpreter lock", "python lock"],
    "mutex":             ["mutex", "mutual exclusion", "s m u text", "m u text", "mutex lock", "locking mechanism", "lock"],
    "cpython":           ["cpython", "c python", "python interpreter", "standard python", "python"],
    "concurrency":       ["concurrency", "concurrent", "parallel", "thread", "threading", "async", "at the same time"],
    "multi-threading":   ["multi-threading", "multithreading", "multi-threaded", "multithreaded", "multiple threads", "multiple native thread", "native thread", "native threads", "threads"],
    "multiprocessing":   ["multiprocessing", "multi processing", "multiple processes", "process pool"],
    "cpu-bound":         ["cpu-bound", "cpubound", "cpu bound", "cpu intensive", "compute bound"],
    "event loop":        ["event loop", "event-loop", "event driven", "call stack", "microtask"],
    "rest api":          ["rest", "restful", "http endpoints", "http api", "get post put delete", "api endpoint"],
    "graphql":           ["graphql", "graph ql", "query language api"],
    "jwt":               ["jwt", "json web token", "token auth", "stateless token", "bearer token"],
    "sql":               ["sql", "relational database", "rdbms", "structured query"],
    "nosql":             ["nosql", "no sql", "non relational", "document db", "mongodb"],
    "acid":              ["acid", "atomicity", "consistency", "isolation", "durability"],
    "microservices":     ["microservices", "micro services", "micro-services", "distributed services", "independent services"],
    "monolith":          ["monolith", "monolithic", "single codebase", "single application", "unified app"],
    "scalability":       ["scalability", "scale", "scaling", "horizontal scaling", "load"],
    "solid":             ["solid", "single responsibility", "open closed", "liskov", "interface segregation", "dependency inversion"],
    "hypothesis testing":["hypothesis testing", "null hypothesis", "p-value", "significance", "test"],
    "correlation":       ["correlation", "correlated", "relationship"],
    "causation":         ["causation", "causal", "cause and effect", "causes"],
}

FILLER_WORDS = {
    "um", "uh", "er", "ah", "like", "you know", "i mean",
    "sort of", "kind of", "maybe", "i guess", "basically",
    "actually", "literally", "right",
}


# ===========================================================================
# STEP 1 - STT NORMALIZATION
# ===========================================================================

def normalize_stt(text: str) -> str:
    """Apply context-aware STT corrections to raw transcription."""
    if not text:
        return ""
    normalized = text.lower()
    for pattern, replacement in STT_CORRECTIONS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return normalized


# ===========================================================================
# STEP 2 - CONCEPT DETECTION
# ===========================================================================

def _concept_present(concept_key: str, normalized_text: str) -> bool:
    """Check whether a concept is present using direct match + synonym table."""
    key_clean = concept_key.lower().strip()
    if key_clean in normalized_text:
        return True
    tokens = key_clean.split()
    if len(tokens) > 1 and all(t in normalized_text for t in tokens):
        return True
    synonyms_for = None
    for canon_key, syn_list in CONCEPT_SYNONYMS.items():
        if key_clean == canon_key or key_clean in syn_list:
            synonyms_for = syn_list
            break
    if synonyms_for:
        if any(s in normalized_text for s in synonyms_for):
            return True
    return False


def _classify_concepts(expected_concepts: List[str], normalized_text: str) -> Dict[str, Any]:
    identified = []
    missing = []
    for concept in expected_concepts:
        if _concept_present(concept, normalized_text):
            identified.append(concept)
        else:
            missing.append(concept)
    total = len(expected_concepts) if expected_concepts else 1
    match_ratio = len(identified) / total
    return {"identified": identified, "missing": missing, "match_ratio": match_ratio, "total_expected": total}


# ===========================================================================
# STEP 3 - SINGLE QUESTION DEEP EVALUATION
# ===========================================================================

def evaluate_one_question(
    question_text: str,
    expected_concepts: List[str],
    reference_answer: str,
    user_answer: str,
    category: str = "Technical"
) -> Dict[str, Any]:
    """
    Deep evidence-based evaluation of a single answered question.
    Dimensions: Concept Coverage, Relevance, Technical Depth,
                Completeness, Explanation Quality.
    """
    if not user_answer or not user_answer.strip():
        return {
            "status": "unanswered",
            "concept_match_label": "No answer recorded",
            "score": 0.0,
            "concepts_expected": expected_concepts,
            "concepts_identified": [],
            "concepts_missing": expected_concepts,
            "dimensions": {},
            "feedback": "No answer was recorded for this question."
        }

    normalized = normalize_stt(user_answer)
    concept_data = _classify_concepts(expected_concepts, normalized)
    identified = concept_data["identified"]
    missing = concept_data["missing"]
    match_ratio = concept_data["match_ratio"]

    # A. Concept Coverage
    if match_ratio >= 0.70:
        coverage_label, coverage_score = "Strong", 5.0
    elif match_ratio >= 0.45:
        coverage_label, coverage_score = "Moderate", 3.5
    elif match_ratio >= 0.20 or len(identified) >= 1:
        coverage_label, coverage_score = "Basic", 2.5
    else:
        coverage_label, coverage_score = "Minimal", 1.5

    # B. Relevance
    q_words = set(re.findall(r"\b\w{4,}\b", question_text.lower()))
    ans_words = set(re.findall(r"\b\w{4,}\b", normalized))
    overlap = len(q_words & ans_words) / max(len(q_words), 1)
    relevance_score = min(5.0, 2.5 + overlap * 5.0)
    relevance_label = "High" if overlap >= 0.3 else ("Moderate" if overlap >= 0.15 else "Low")

    # C. Technical Depth
    word_count = len(user_answer.split())
    if word_count >= 60:
        depth_label, depth_score = "Moderate to High", 4.0
    elif word_count >= 30:
        depth_label, depth_score = "Basic to Moderate", 3.0
    elif word_count >= 12:
        depth_label, depth_score = "Basic", 2.0
    else:
        depth_label, depth_score = "Very shallow", 1.0

    # D. Completeness
    comparison_keywords = ["compare", "difference", "versus", "vs", "between"]
    is_comparison = any(kw in question_text.lower() for kw in comparison_keywords)
    completeness_score, completeness_label = 3.0, "Partial"
    if is_comparison:
        q_entities = [c.lower() for c in expected_concepts[:2]]
        both_found = all(_concept_present(e, normalized) for e in q_entities)
        if both_found:
            completeness_score, completeness_label = 4.0, "Good"
        else:
            completeness_score, completeness_label = 2.0, "Incomplete"
    elif match_ratio >= 0.60:
        completeness_score, completeness_label = 4.5, "Good"
    elif match_ratio >= 0.35:
        completeness_score, completeness_label = 3.0, "Partial"
    else:
        completeness_score, completeness_label = 1.5, "Incomplete"

    # E. Explanation Quality
    sentences = [s.strip() for s in re.split(r"[.!?]+", user_answer) if s.strip()]
    sentence_count = len(sentences)
    filler_count = sum(1 for fw in FILLER_WORDS if fw in normalized)
    filler_density = filler_count / max(word_count, 1)
    if sentence_count >= 3 and filler_density < 0.04:
        quality_label, quality_score = "Structured", 4.5
    elif sentence_count >= 2 or (word_count >= 20 and filler_density < 0.08):
        quality_label, quality_score = "Moderate", 3.0
    else:
        quality_label, quality_score = "Fragmented", 1.8

    # Composite score: Coverage 40%, Completeness 25%, Depth 20%, Quality 15%
    raw_score = (coverage_score * 0.40 + completeness_score * 0.25 +
                 depth_score * 0.20 + quality_score * 0.15)
    final_score = round(min(5.0, max(1.0, raw_score)), 1)

    # Match label for badge
    if match_ratio >= 0.65:
        match_label = "Strong concept match"
    elif match_ratio >= 0.35:
        match_label = "Moderate concept match"
    elif len(identified) > 0:
        match_label = "Partial concept match"
    else:
        match_label = "Weak concept match"

    # Narrative feedback
    id_str = ", ".join(identified) if identified else "none of the expected concepts"
    miss_str = ", ".join(missing[:3]) if missing else "none"
    if match_ratio >= 0.65:
        feedback = (f"Strong answer covering key concepts. Demonstrated: {id_str}. "
                    + (f"Minor gaps in: {miss_str}." if missing else "All key concepts addressed."))
    elif match_ratio >= 0.35:
        feedback = (f"Showed foundational understanding. Demonstrated: {id_str}. "
                    f"Concepts to strengthen: {miss_str}. Consider structuring your explanation more clearly.")
    elif len(identified) >= 1:
        feedback = (f"Touched on relevant ideas ({id_str}), but lacked coverage of core concepts: {miss_str}. "
                    f"The explanation needs more depth.")
    else:
        feedback = (f"Answer did not clearly demonstrate expected concepts: {', '.join(expected_concepts[:4])}. "
                    f"Review the topic and practise structured explanations.")

    return {
        "status": "answered",
        "concept_match_label": match_label,
        "score": final_score,
        "concepts_expected": expected_concepts,
        "concepts_identified": identified,
        "concepts_missing": missing,
        "dimensions": {
            "concept_coverage":    {"label": coverage_label,    "score": coverage_score},
            "relevance":           {"label": relevance_label,   "score": round(relevance_score, 1)},
            "technical_depth":     {"label": depth_label,       "score": depth_score},
            "completeness":        {"label": completeness_label,"score": completeness_score},
            "explanation_quality": {"label": quality_label,     "score": quality_score},
        },
        "feedback": feedback,
        "word_count": word_count,
        "sentence_count": sentence_count,
    }


# ===========================================================================
# STEP 4 - SESSION COMMUNICATION SCORE
# ===========================================================================

def evaluate_session_communication(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate communication fluency based ONLY on answered questions."""
    answered_list = [
        a for a in answers
        if a.get("status") != "skipped" and a.get("transcript_text", "").strip()
    ]
    if not answered_list:
        return {
            "score": None,
            "details": "No spoken answers recorded. Communication cannot be assessed.",
            "evidence_level": "none"
        }
    total_words, total_sentences, total_filler = 0, 0, 0
    unique_words: set = set()
    for a in answered_list:
        text = a.get("transcript_text", "")
        normalized = normalize_stt(text)
        words = normalized.split()
        total_words += len(words)
        unique_words.update(words)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        total_sentences += len(sentences)
        total_filler += sum(1 for fw in FILLER_WORDS if fw in normalized)
    n = len(answered_list)
    avg_words = total_words / n
    vocab_diversity = len(unique_words) / max(total_words, 1)
    filler_ratio = total_filler / max(total_words, 1)
    comm_score = 3.0
    if 30 <= avg_words <= 150:
        comm_score += 0.7
    elif avg_words > 150:
        comm_score += 0.3
    else:
        comm_score -= 0.7
    if vocab_diversity >= 0.55:
        comm_score += 0.5
    elif vocab_diversity < 0.35:
        comm_score -= 0.3
    if filler_ratio < 0.03:
        comm_score += 0.4
    elif filler_ratio > 0.08:
        comm_score -= 0.5
    avg_sent = total_sentences / n
    if avg_sent >= 3:
        comm_score += 0.3
    final = round(min(5.0, max(1.0, comm_score)), 1)
    if n >= 3:
        evidence_level = "sufficient"
    elif n == 2:
        evidence_level = "limited"
    else:
        evidence_level = "minimal - based on a single answer"
    return {
        "score": final,
        "avg_words_per_answer": round(avg_words, 1),
        "vocab_diversity": round(vocab_diversity, 3),
        "filler_ratio": round(filler_ratio, 3),
        "evidence_level": evidence_level,
        "fluency": "High" if final >= 4.0 else ("Moderate" if final >= 3.0 else "Needs Improvement"),
        "details": (
            f"Communication assessed across {n} spoken answer(s). "
            f"Average response length: {round(avg_words)} words. "
            f"Vocabulary diversity: {round(vocab_diversity * 100)}%. "
            f"Filler word density: {round(filler_ratio * 100, 1)}%."
        )
    }


# ===========================================================================
# STEP 5 - SESSION CONFIDENCE SCORE
# ===========================================================================

def evaluate_session_confidence(answers: List[Dict[str, Any]], total_questions: int) -> Dict[str, Any]:
    """Confidence estimated from observable session signals only. No psychological claims."""
    answered_list = [
        a for a in answers
        if a.get("status") != "skipped" and a.get("transcript_text", "").strip()
    ]
    if not answered_list:
        return {
            "score": 1.5,
            "evidence_level": "none",
            "details": (
                "All questions were skipped. No observable answer data exists "
                "to assess session confidence signals."
            )
        }
    completion_ratio = len(answered_list) / max(total_questions, 1)
    base_conf = 2.5 + (completion_ratio * 1.5)
    filler_count, total_words = 0, 0
    word_lengths = []
    for a in answered_list:
        text = a.get("transcript_text", "")
        normalized = normalize_stt(text)
        words = normalized.split()
        total_words += len(words)
        word_lengths.append(len(words))
        for fw in FILLER_WORDS:
            filler_count += normalized.count(fw)
    filler_ratio = filler_count / max(total_words, 1)
    if filler_ratio < 0.03:
        base_conf += 0.5
    elif filler_ratio > 0.08:
        base_conf -= 0.5
    if len(word_lengths) >= 2:
        min_len = min(word_lengths)
        if min_len >= 20:
            base_conf += 0.4
        elif min_len < 8:
            base_conf -= 0.3
    final = round(min(5.0, max(1.0, base_conf)), 1)
    evidence_level = ("minimal - one answer sampled" if len(answered_list) == 1
                      else ("limited" if len(answered_list) == 2 else "sufficient"))
    if filler_ratio > 0.08:
        signal_note = (
            "The response contained noticeable hesitation markers, which suggests "
            "the candidate may benefit from practising more structured technical explanations."
        )
    elif completion_ratio < 0.5:
        signal_note = (
            f"Only {len(answered_list)} of {total_questions} questions were attempted. "
            "Willingness to engage consistently across questions is an important interview signal."
        )
    else:
        signal_note = "The candidate engaged with the available questions with reasonable continuity."
    return {
        "score": final,
        "filler_count": filler_count,
        "completion_ratio": round(completion_ratio * 100, 1),
        "evidence_level": evidence_level,
        "confidence_level": "Confident" if final >= 4.0 else ("Steady" if final >= 3.0 else "Developing"),
        "details": signal_note
    }


# ===========================================================================
# STEP 6 - EVIDENCE-BASED STRENGTHS & RECOMMENDATIONS
# ===========================================================================

def _build_strengths(
    question_evals: List[Dict[str, Any]],
    resume_skills: List[str],
    target_role: str
) -> List[str]:
    """Strengths are drawn only from what the candidate actually demonstrated."""
    strengths = []
    for qe in question_evals:
        if qe.get("status") == "skipped":
            continue
        identified = qe.get("concepts_identified", [])
        category = qe.get("category", "the topic")
        match_label = qe.get("concept_match_label", "")
        q_score = qe.get("technical_score")
        if identified and (q_score is not None and q_score >= 3.0):
            id_str = ", ".join(identified[:3])
            if "Strong" in match_label:
                strengths.append(
                    f"Demonstrated strong understanding of {category}: accurately covered {id_str}."
                )
            elif "Moderate" in match_label or "Partial" in match_label:
                strengths.append(
                    f"Showed foundational knowledge in {category}: communicated concepts including {id_str}."
                )
    answered_categories = [qe.get("category", "") for qe in question_evals if qe.get("status") != "skipped"]
    if resume_skills and answered_categories:
        relevant_skills = [
            s for s in resume_skills
            if s.lower() in target_role.lower() or any(s.lower() in cat.lower() for cat in answered_categories)
        ]
        if relevant_skills:
            strengths.append(
                f"Resume skills ({', '.join(relevant_skills[:3])}) are relevant to "
                f"the {target_role} role and align with the topics evaluated."
            )
    return strengths[:4] if strengths else []


def _build_recommendations(question_evals: List[Dict[str, Any]], target_role: str) -> List[str]:
    """Recommendations derived strictly from question -> expected -> missing -> role."""
    recs = []
    for qe in question_evals:
        if qe.get("status") == "skipped":
            recs.append(
                f"Review the topic of {qe.get('category', 'this area')}: the question was skipped during the session."
            )
            continue
        missing = qe.get("concepts_missing", [])
        category = qe.get("category", "the topic")
        match_label = qe.get("concept_match_label", "")
        if missing and ("Weak" in match_label or "Partial" in match_label or "Moderate" in match_label):
            miss_str = ", ".join(missing[:3])
            recs.append(
                f"In {category}: deepen your understanding of {miss_str}. "
                f"Practise explaining these concepts with concrete examples."
            )
        elif missing:
            recs.append(f"Strengthen coverage of {', '.join(missing[:2])} in {category}.")
    seen, unique_recs = set(), []
    for r in recs:
        key = r[:50]
        if key not in seen:
            seen.add(key)
            unique_recs.append(r)
    return unique_recs[:5]


def _build_weaknesses(question_evals: List[Dict[str, Any]]) -> List[str]:
    """Weaknesses come from observable evaluation evidence only."""
    weaknesses = []
    for qe in question_evals:
        if qe.get("status") == "skipped":
            weaknesses.append(
                f"Question on {qe.get('category', 'unknown topic')} was skipped — no technical evidence available."
            )
            continue
        match_label = qe.get("concept_match_label", "")
        missing = qe.get("concepts_missing", [])
        category = qe.get("category", "Technical")
        if "Weak" in match_label or "No answer" in match_label:
            weaknesses.append(f"Answer for {category} did not demonstrate sufficient concept coverage.")
        elif "Partial" in match_label and missing:
            weaknesses.append(f"Concepts like {', '.join(missing[:2])} were not fully addressed in {category}.")
    return weaknesses[:4]


# ===========================================================================
# MASTER ENTRY POINT
# ===========================================================================

def evaluate_entire_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master post-session analysis.
    Enforces: ANSWER QUALITY != ANSWER COVERAGE
    Skipped questions affect coverage only, NOT technical_score.
    """
    questions     = session_data.get("questions", [])
    raw_answers   = session_data.get("answers", [])
    target_role   = session_data.get("target_role", "Candidate")
    resume_skills = session_data.get("resume_skills", [])
    session_code  = session_data.get("session_code", "")
    total_q       = len(questions)

    # Build answer lookup by id and question_code
    answers_by_qid: Dict[str, Dict] = {}
    for ans in raw_answers:
        qid = str(ans.get("question_id") or ans.get("question_code") or "")
        qcode = str(ans.get("question_code") or "")
        if qid:
            answers_by_qid[qid] = ans
        if qcode:
            answers_by_qid[qcode] = ans

    question_evaluations = []
    technical_scores: List[float] = []
    answered_count = 0
    skipped_count  = 0

    for q in questions:
        qid   = str(q.get("id") or q.get("question_code") or "")
        qcode = q.get("question_code", f"Q{qid}")
        q_text        = q.get("question_text", "")
        expected_conc = q.get("key_concepts", [])
        ref_ans       = q.get("reference_answer", "")
        category      = q.get("category", "Technical")
        difficulty    = q.get("difficulty", "Intermediate")

        user_ans_data = answers_by_qid.get(qid) or answers_by_qid.get(qcode)
        is_skipped = (
            not user_ans_data
            or user_ans_data.get("status") == "skipped"
            or not user_ans_data.get("transcript_text", "").strip()
        )

        if is_skipped:
            skipped_count += 1
            question_evaluations.append({
                "question_id":         qid,
                "question_code":       qcode,
                "question_text":       q_text,
                "category":            category,
                "difficulty":          difficulty,
                "status":              "skipped",
                "user_answer":         "[Question skipped - no answer recorded]",
                "concepts_expected":   expected_conc,
                "concepts_identified": [],
                "concepts_missing":    expected_conc,
                "concept_match":       "Skipped",
                "concept_match_label": "Skipped",
                "technical_score":     None,
                "dimensions":          {},
                "feedback":            "This question was skipped. No technical evaluation was performed."
            })
        else:
            answered_count += 1
            user_text = user_ans_data.get("transcript_text", "")
            eval_res = evaluate_one_question(
                question_text=q_text,
                expected_concepts=expected_conc,
                reference_answer=ref_ans,
                user_answer=user_text,
                category=category
            )
            technical_scores.append(eval_res["score"])
            question_evaluations.append({
                "question_id":         qid,
                "question_code":       qcode,
                "question_text":       q_text,
                "category":            category,
                "difficulty":          difficulty,
                "status":              "answered",
                "user_answer":         user_text,
                "concepts_expected":   eval_res["concepts_expected"],
                "concepts_identified": eval_res["concepts_identified"],
                "concepts_missing":    eval_res["concepts_missing"],
                "concept_match":       eval_res["concept_match_label"],
                "concept_match_label": eval_res["concept_match_label"],
                "technical_score":     eval_res["score"],
                "dimensions":          eval_res.get("dimensions", {}),
                "feedback":            eval_res["feedback"]
            })

    # Check if we have any answers
    if answered_count == 0:
        avg_tech_score = None
        comm_score = None
        conf_score = None
        overall_score = None
        
        tech_evidence_note = "Technical answer quality could not be assessed because no questions were answered during this session."
        limited_evidence_note = "No questions were answered during this interview session. Technical, communication, and confidence scores cannot be reliably evaluated."
        
        strengths = ["No strengths could be reliably identified from answered questions because no questions were answered."]
        weaknesses = []
        recommendations = [
            "Attempt each question so that your technical knowledge can be evaluated.",
            "Review the listed interview topics before attempting another round.",
            "Practice answering technical questions verbally instead of skipping them."
        ]
        
        comm_details = "Communication fluency could not be evaluated because no spoken answers were provided."
        conf_details = "Confidence could not be reliably evaluated because no spoken answers were recorded."
        
        comm_evidence_level = "none"
        conf_evidence_level = "none"
        
        # We can still calculate coverage though
        answer_coverage_ratio = 0.0
        answer_coverage_pct   = 0.0
        answered_display      = f"0/{total_q}"
    else:
        # ANSWER QUALITY: only from answered questions
        avg_tech_score = round(sum(technical_scores) / len(technical_scores), 1)
        tech_evidence_note = None

        # Limited evidence acknowledgment
        limited_evidence_note = None
        if answered_count < total_q:
            pct = round(answered_count / total_q * 100)
            limited_evidence_note = (
                f"Technical performance is based on {answered_count} answered question(s) out of {total_q} "
                f"({pct}% coverage), so the result represents limited interview evidence. "
                f"A fuller assessment requires attempting all questions."
            )

        # ANSWER COVERAGE: separate metric
        answer_coverage_ratio = round(answered_count / max(total_q, 1), 4)
        answer_coverage_pct   = round(answer_coverage_ratio * 100, 1)
        answered_display      = f"{answered_count}/{total_q}"

        # Communication and Confidence
        comm_result = evaluate_session_communication(raw_answers)
        conf_result = evaluate_session_confidence(raw_answers, total_q)
        comm_score  = comm_result.get("score")
        conf_score  = conf_result.get("score")
        
        comm_details = comm_result.get("details", "")
        conf_details = conf_result.get("details", "")
        comm_evidence_level = comm_result.get("evidence_level", "unknown")
        conf_evidence_level = conf_result.get("evidence_level", "unknown")

        # OVERALL SCORE with adaptive weights
        weights = {"tech": 0.50, "comm": 0.25, "conf": 0.25}
        if comm_score is None and conf_score is None:
            weights = {"tech": 1.0, "comm": 0.0, "conf": 0.0}
            comm_score, conf_score = 0.0, 0.0
        elif comm_score is None:
            weights = {"tech": 0.60, "comm": 0.0, "conf": 0.40}
            comm_score = 0.0
        elif conf_score is None:
            weights = {"tech": 0.60, "comm": 0.40, "conf": 0.0}
            conf_score = 0.0

        if avg_tech_score > 0 or comm_score > 0 or conf_score > 0:
            overall_score = round(
                avg_tech_score * weights["tech"] +
                comm_score     * weights["comm"] +
                conf_score     * weights["conf"], 1
            )
        else:
            overall_score = 0.0

        # Evidence-based qualitative feedback
        strengths       = _build_strengths(question_evaluations, resume_skills, target_role)
        weaknesses      = _build_weaknesses(question_evaluations)
        recommendations = _build_recommendations(question_evaluations, target_role)

    return {
        "session_code":           session_code,
        "target_role":            target_role,
        "total_questions":        total_q,
        "answered_count":         answered_count,
        "skipped_count":          skipped_count,
        "unanswered_count":       total_q - answered_count - skipped_count,
        "answered_display":       answered_display,
        "answered_percentage":    answer_coverage_pct,
        "answer_coverage_ratio":  answer_coverage_ratio,
        "overall_score":          overall_score,
        "technical_score":        avg_tech_score,
        "communication_score":    comm_score,
        "confidence_score":       conf_score,
        "tech_evidence_note":     tech_evidence_note,
        "limited_evidence_note":  limited_evidence_note,
        "comm_evidence_level":    comm_evidence_level,
        "conf_evidence_level":    conf_evidence_level,
        "comm_details":           comm_details,
        "conf_details":           conf_details,
        "strengths":              strengths,
        "weaknesses":             weaknesses,
        "recommendations":        recommendations,
        "question_evaluations":   question_evaluations,
    }
