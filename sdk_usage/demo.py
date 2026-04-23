"""
SDK Usage Example — Online Exam Proctoring System
Author: AI Intern @ aumne.ai

Instructions to generate the SDK:
  npm install -g @openapitools/openapi-generator-cli
  openapi-generator-cli generate \
      -i http://localhost:8000/openapi.json \
      -g python \
      -o exam_sdk

Then install it:
  pip install -e exam_sdk/

Then run this script:
  python sdk_usage/demo.py
"""

import sys
import time

# ─── After SDK generation, these imports become available ───────────────────
# from exam_sdk.api.exams_api import ExamsApi
# from exam_sdk.api.submissions_api import SubmissionsApi
# from exam_sdk import ApiClient, Configuration

# ─── Until then, we demonstrate equivalent usage with requests ───────────────
import requests

BASE_URL = "http://localhost:8000"


def banner(msg: str):
    print(f"\n{'═'*60}")
    print(f"  {msg}")
    print('═'*60)


def demo():
    banner("ProctorAI SDK Demo — aumne.ai")

    # ── 1. Create an exam ────────────────────────────────────────
    banner("Step 1: Create Exam")
    r = requests.post(f"{BASE_URL}/exams/", json={
        "title": "AI & ML Internship Assessment",
        "duration": 60
    })
    r.raise_for_status()
    exam = r.json()
    exam_id = exam["id"]
    print(f"  ✅ Created exam: '{exam['title']}' (ID={exam_id}, duration={exam['duration']}min)")

    # ── 2. List exams ────────────────────────────────────────────
    banner("Step 2: List All Exams")
    r = requests.get(f"{BASE_URL}/exams/")
    r.raise_for_status()
    for e in r.json():
        print(f"  📋 [{e['id']}] {e['title']} — {e['duration']} min")

    # ── 3. Clean submission ──────────────────────────────────────
    banner("Step 3: Submit Clean Answers")
    r = requests.post(f"{BASE_URL}/exams/{exam_id}/submit", json={
        "user_name": "alice_clean",
        "answers": {
            "q1": "Supervised learning uses labeled data; unsupervised finds patterns without labels.",
            "q2": "def reverse(head):\n  prev = None\n  while head:\n    nxt = head.next\n    head.next = prev\n    prev = head\n    head = nxt\n  return prev"
        },
        "time_taken_seconds": 2100,
        "paste_detected": False
    })
    r.raise_for_status()
    sub = r.json()
    print(f"  ✅ Submission ID={sub['id']}, suspicious={sub['suspicious']}, flags={sub['flag_reasons']}")

    # ── 4. Flagged submission — copy-paste ───────────────────────
    banner("Step 4: Submit with Copy-Paste (should flag)")
    r = requests.post(f"{BASE_URL}/exams/{exam_id}/submit", json={
        "user_name": "bob_cheater",
        "answers": {
            "q1": "def foo(): pass",
            "q2": "def foo(): pass"   # identical answer
        },
        "time_taken_seconds": 1800,
        "paste_detected": True
    })
    r.raise_for_status()
    sub = r.json()
    print(f"  🚨 Submission ID={sub['id']}, suspicious={sub['suspicious']}")
    for flag in sub["flag_reasons"]:
        print(f"     └─ {flag}")

    # ── 5. Flagged submission — too fast ─────────────────────────
    banner("Step 5: Submit Suspiciously Fast")
    r = requests.post(f"{BASE_URL}/exams/{exam_id}/submit", json={
        "user_name": "charlie_speedrun",
        "answers": {"q1": "I guessed"},
        "time_taken_seconds": 25,
        "paste_detected": False
    })
    r.raise_for_status()
    sub = r.json()
    print(f"  🚨 suspicious={sub['suspicious']}, flags={sub['flag_reasons']}")

    # ── 6. List flagged submissions ──────────────────────────────
    banner("Step 6: List Flagged Submissions")
    r = requests.get(f"{BASE_URL}/submissions/?flagged_only=true")
    r.raise_for_status()
    for s in r.json():
        print(f"  ⚠️  [{s['id']}] {s['user_name']} — {s['flag_reasons']}")

    # ── 7. Health check ──────────────────────────────────────────
    banner("Step 7: Health Check")
    r = requests.get(f"{BASE_URL}/health")
    print(f"  {r.json()}")

    banner("Demo Complete ✅")
    print("""
  With the generated SDK, the above calls become:

    from exam_sdk.api.exams_api import ExamsApi
    from exam_sdk import ApiClient
    client = ApiClient()
    api = ExamsApi(client)

    exam = api.create_exam_exams_post({"title": "Test", "duration": 60})
    result = api.submit_exam_exams_id_submit_post(exam.id, {...})
""")


if __name__ == "__main__":
    try:
        demo()
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend not running. Start it first:")
        print("   cd backend && python main.py")
        sys.exit(1)


def demo_advanced():
    """Showcase AI-powered features: semantic similarity + tab detection"""
    banner("ADVANCED DEMO — AI Proctoring Features")

    # Create exam
    exam = requests.post(f"{BASE_URL}/exams/", json={
        "title": "Advanced AI Proctoring Test",
        "duration": 60
    }).json()
    eid = exam["id"]

    # Tab-switch flagging
    banner("Tab-Switch Detection")
    r = requests.post(f"{BASE_URL}/exams/{eid}/submit", json={
        "user_name": "tab_switcher",
        "answers": {"q1": "Supervised learning uses labeled data to train models."},
        "time_taken_seconds": 2000,
        "paste_detected": False,
        "tab_switch_count": 7   # ← detected by browser JS
    })
    sub = r.json()
    print(f"  suspicious={sub['suspicious']}")
    for f in sub["flag_reasons"]:
        print(f"  └─ {f}")

    # Semantic similarity (requires Ollama running)
    banner("Semantic Similarity (requires: ollama serve && ollama pull llama3)")
    r = requests.post(f"{BASE_URL}/exams/{eid}/submit", json={
        "user_name": "paraphraser",
        "answers": {
            "q1": "Supervised machine learning trains a model on data that has been labelled.",
            "q2": "In supervised ML, we use labeled datasets to train our prediction model."
            # ^ Paraphrased — rule-based misses this, LLM catches it
        },
        "time_taken_seconds": 1900,
        "paste_detected": False,
        "tab_switch_count": 0
    })
    sub = r.json()
    print(f"  suspicious={sub['suspicious']}, flags={len(sub['flag_reasons'])}")
    for f in sub["flag_reasons"]:
        print(f"  └─ {f}")
    if sub.get("audit_log"):
        print(f"\n  🤖 AI Audit Note:\n  {sub['audit_log']}")
    else:
        print("  (Start Ollama to see AI audit log and semantic detection)")

    banner("All Done ✅")


if __name__ == "__main__":
    try:
        demo()
        demo_advanced()
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend not running. Start it first:")
        print("   cd backend && python main.py")
        sys.exit(1)
