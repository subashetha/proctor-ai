"""
proctoring.py — AI-assisted cheating detection engine
Part of: Online Exam Proctoring System @ aumne.ai

Detection strategies:
  1. Copy-paste detected     (frontend flag OR identical answers)
  2. Semantic similarity     (LLM via Ollama — catches paraphrased cheating)
  3. Abnormally fast submit  (< 20% of allotted time)
  4. Long inactivity/OT      (> 110% of allotted time)
  5. Blank submission        (all answers empty)
  6. Tab-switch events       (frontend focus-loss detection)

AI Layer:
  - Uses Ollama (local LLM, free, no API key) for semantic analysis
  - Model: llama3 (or any model pulled via `ollama pull llama3`)
  - Falls back to rule-based detection if Ollama is not running
"""

import json
import logging
import requests as http_requests
from itertools import combinations
from typing import List, Optional, Tuple

from schemas import SubmissionCreate, SuspiciousFlag

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

FAST_SUBMIT_RATIO       = 0.20    # flag if < 20% of duration used
OVERTIME_RATIO          = 1.10    # flag if > 110% of duration used
SIMILARITY_THRESHOLD    = 0.80    # LLM similarity score >= 80% → flag
OLLAMA_URL              = "http://localhost:11434/api/generate"
OLLAMA_MODEL            = "llama3"   # change to "mistral", "phi3", etc. if needed
OLLAMA_TIMEOUT          = 30         # seconds


# ── Ollama LLM Interface ───────────────────────────────────────────────────────

def _call_ollama(prompt: str) -> Optional[str]:
    """Send a prompt to a local Ollama model. Returns response text or None."""
    try:
        response = http_requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}   # deterministic for scoring
            },
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except http_requests.exceptions.ConnectionError:
        logger.warning("Ollama not running — skipping LLM analysis. Start with: ollama serve")
        return None
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return None


def _llm_similarity_score(answer_a: str, answer_b: str) -> Optional[Tuple[float, str]]:
    """
    Ask the LLM to rate how semantically similar two answers are (0.0 – 1.0).
    Returns (score, reason) or None if Ollama is unavailable.
    """
    prompt = f"""You are a strict academic integrity checker.

Compare these two exam answers and rate how semantically similar they are.
Even if the wording is different, if they express the same core ideas, rate them highly.

Answer A:
{answer_a}

Answer B:
{answer_b}

Respond with ONLY a JSON object in this exact format, nothing else:
{{"similarity": 0.85, "reason": "Both answers describe the same concept using different words"}}

The similarity score must be between 0.0 (completely different) and 1.0 (identical meaning)."""

    raw = _call_ollama(prompt)
    if not raw:
        return None

    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        score = float(data.get("similarity", 0))
        reason = data.get("reason", "")
        return score, reason
    except Exception as e:
        logger.warning(f"Failed to parse LLM similarity response: {raw!r} — {e}")
        return None


def _llm_audit_explanation(flags: List[str], user_name: str, exam_title: str) -> Optional[str]:
    """
    Ask the LLM to generate a human-readable audit explanation for the flags.
    """
    if not flags:
        return None

    prompt = f"""You are an academic integrity officer writing a brief audit note.

Student: {user_name}
Exam: {exam_title}
Detected violations: {', '.join(flags)}

Write a concise 2-3 sentence professional audit note explaining what was detected
and why it is considered suspicious. Be factual and neutral. Do not be accusatory.
Respond with plain text only, no bullet points."""

    return _call_ollama(prompt)


# ── Core Detection Engine ──────────────────────────────────────────────────────

def analyze_submission(
    submission: SubmissionCreate,
    exam,
    db=None
) -> List[SuspiciousFlag]:
    """
    Full proctoring analysis pipeline.
    Runs rule-based checks first, then LLM semantic analysis.
    """
    flags: List[SuspiciousFlag] = []
    answers = submission.answers or {}
    duration_seconds = exam.duration * 60
    time_taken = submission.time_taken_seconds
    non_empty = {k: v.strip() for k, v in answers.items() if v.strip()}

    # ── Rule 1: Frontend paste event ────────────────────────────────────────
    if submission.paste_detected:
        flags.append(SuspiciousFlag(reason="COPY_PASTE_DETECTED"))

    # ── Rule 2: Exact duplicate answers ─────────────────────────────────────
    values = list(non_empty.values())
    if len(values) > 1 and len(set(values)) < len(values):
        if not any(f.reason == "COPY_PASTE_DETECTED" for f in flags):
            flags.append(SuspiciousFlag(reason="COPY_PASTE_DETECTED"))

    # ── Rule 3: Blank submission ─────────────────────────────────────────────
    if not non_empty:
        flags.append(SuspiciousFlag(reason="BLANK_SUBMISSION"))

    # ── Rule 4: Time anomalies ───────────────────────────────────────────────
    if time_taken is not None:
        threshold_fast = int(duration_seconds * FAST_SUBMIT_RATIO)
        if time_taken < threshold_fast:
            flags.append(SuspiciousFlag(
                reason=f"SUSPICIOUSLY_FAST_SUBMISSION (took {time_taken}s, min expected {threshold_fast}s)"
            ))

        threshold_ot = int(duration_seconds * OVERTIME_RATIO)
        if time_taken > threshold_ot:
            flags.append(SuspiciousFlag(
                reason=f"LONG_INACTIVITY_OR_OVERTIME (took {time_taken}s, limit {threshold_ot}s)"
            ))

    # ── Rule 5: Tab-switch events ────────────────────────────────────────────
    tab_switches = getattr(submission, "tab_switch_count", 0) or 0
    if tab_switches >= 3:
        flags.append(SuspiciousFlag(
            reason=f"FOCUS_LOSS_DETECTED ({tab_switches} tab-switches recorded)"
        ))

    # ── AI Layer: Semantic similarity via Ollama ─────────────────────────────
    if len(non_empty) >= 2:
        pairs = list(combinations(non_empty.items(), 2))
        for (qid_a, ans_a), (qid_b, ans_b) in pairs:
            if ans_a == ans_b:
                continue  # already caught by exact-match rule
            if len(ans_a) < 30 or len(ans_b) < 30:
                continue  # too short for meaningful comparison

            result = _llm_similarity_score(ans_a, ans_b)
            if result is None:
                continue  # Ollama not available — skip silently

            score, reason = result
            if score >= SIMILARITY_THRESHOLD:
                flags.append(SuspiciousFlag(
                    reason=(
                        f"AI_SEMANTIC_SIMILARITY_DETECTED "
                        f"({qid_a} vs {qid_b}: {int(score*100)}% similar — {reason})"
                    )
                ))

    return flags


def generate_audit_log(
    flags: List[SuspiciousFlag],
    user_name: str,
    exam_title: str
) -> Optional[str]:
    """
    Generate a plain-English AI audit explanation for a flagged submission.
    Returns None if no flags or Ollama unavailable.
    """
    if not flags:
        return None
    flag_codes = [f.reason.split("(")[0].strip() for f in flags]
    return _llm_audit_explanation(flag_codes, user_name, exam_title)
