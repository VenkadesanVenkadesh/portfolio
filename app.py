"""
Portfolio backend for Venkadesan Marimuthu.

Serves the single-page portfolio and powers two small pieces of real
server-side logic:

  * POST /api/search   -- a lightweight keyword-retrieval engine that
    scores the portfolio's own content (skills, projects, experience)
    against a visitor's query, and returns ranked "chunks" -- a nod to
    the RAG pipeline this portfolio is advertising.

  * POST /api/contact   -- validates and stores contact-form messages.

Run with:  python app.py
"""

import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
CONTACT_LOG = BASE_DIR / "contact_messages.json"

# ---------------------------------------------------------------------------
# Content -- single source of truth, rendered into the page by Jinja and
# also indexed by the search endpoint below.
# ---------------------------------------------------------------------------

PROFILE = {
    "name": "Venkadesan Marimuthu",
    "role": "Python Developer",
    "tagline": "Backend systems, machine learning, and retrieval pipelines.",
    "location": "Chennai, Tamil Nadu, India",
    "email": "mvenkadesan58@gmail.com",
    "phone": "+91 6379696076",
    "github": "https://github.com/VenkadesanVenkadesh",
    "linkedin": "https://www.linkedin.com/in/venkadesan-marimuthu-960630275/",
    "summary": (
        "Python Developer with hands-on experience building backend "
        "applications using Python and Flask, developing machine learning "
        "models, and working with REST APIs and relational databases. "
        "Currently building a custom Retrieval-Augmented Generation (RAG) "
        "pipeline from scratch, covering text chunking, embedding "
        "generation, and semantic retrieval."
    ),
}

SKILLS = [
    {"category": "Languages", "items": ["Python", "SQL", "HTML", "CSS"]},
    {"category": "Frameworks & Libraries", "items": ["Flask", "Pandas", "NumPy", "Scikit-learn", "Matplotlib", "OpenCV"]},
    {"category": "AI / Machine Learning", "items": ["RAG Pipelines", "Text Embeddings", "Chunking", "Semantic Search", "Classification Models"]},
    {"category": "Backend", "items": ["REST APIs", "CRUD Operations", "MySQL Integration"]},
    {"category": "Tools", "items": ["Git", "GitHub", "Jupyter", "Google Colab", "Power BI", "Excel"]},
]

PROJECTS = [
    {
        "id": "REC_001",
        "title": "Retrieval-Augmented Generation (RAG) Pipeline",
        "status": "In Progress",
        "tags": ["Python", "Embeddings", "Vector Retrieval", "NLP"],
        "description": (
            "Custom RAG pipeline built from scratch: document chunking, "
            "text embedding generation, and semantic retrieval, with the "
            "retrieval layer feeding the most relevant chunks into a "
            "generation step. Currently tuning chunking strategy and "
            "retrieval accuracy."
        ),
        "link": "",
    },
    {
        "id": "REC_002",
        "title": "CRUD Application using Flask",
        "status": "Complete",
        "tags": ["Python", "Flask", "MySQL", "HTML", "CSS"],
        "description": (
            "Full-stack CRUD web application with RESTful routes for "
            "Create, Read, Update, and Delete operations, secure MySQL "
            "integration, and optimized SQL queries."
        ),
        "link": "",
    },
    {
        "id": "REC_003",
        "title": "Diabetes Prediction Model",
        "status": "Complete",
        "tags": ["Python", "Pandas", "NumPy", "Scikit-learn"],
        "description": (
            "Classification model to predict diabetes risk. Preprocessing, "
            "feature engineering, and EDA with Pandas/NumPy; compared "
            "Random Forest, Naive Bayes, and KNN on accuracy, precision, "
            "and recall."
        ),
        "link": "",
    },
    {
        "id": "REC_004",
        "title": "Loan Approval Prediction Model",
        "status": "Complete",
        "tags": ["Python", "Pandas", "NumPy", "Matplotlib"],
        "description": (
            "Predictive model reaching 80% accuracy for loan approval. "
            "Included data cleaning, missing-value handling, feature "
            "scaling, and comparison of multiple classifiers."
        ),
        "link": "",
    },
    {
        "id": "REC_005",
        "title": "Object Sorting System Using Robotic Arm",
        "status": "Complete",
        "tags": ["Python", "OpenCV", "Arduino", "Robotics"],
        "description": (
            "Automated object detection and sorting system: OpenCV for "
            "color/shape recognition, a robotic arm on Arduino for "
            "pick-and-place, and a Python control layer tying camera "
            "input to hardware commands."
        ),
        "link": "",
    },
]

EXPERIENCE = [
    {
        "role": "Process Associate",
        "org": "Prochant India Pvt Ltd, Chennai",
        "dates": "Sept 2024 -- July 2026",
        "points": [
            "Verified patient insurance coverage, benefits, and policy details for eligibility verification (EV), ensuring compliance and minimizing claim denials.",
            "Managed and processed fax-based patient information, insurance details, and authorization documents, maintaining accurate records and timely communication.",
        ],
    },
    {
        "role": "Corporate Trainer",
        "org": "Skill-Lync, Chennai",
        "dates": "Sept 2023 -- Dec 2023",
        "points": [
            "Conducted IoT training under the Naan Mudhalvan Scheme, Government of Tamil Nadu.",
            "Delivered hands-on training in C++, Arduino, and ESP8266 for embedded IoT applications.",
            "Trained 100+ students in Python and IoT fundamentals, achieving 95% positive feedback.",
        ],
    },
]

EDUCATION = {
    "degree": "B.E. -- Information Technology",
    "school": "Annamalai University, Chidambaram, Tamil Nadu",
    "dates": "2019 -- 2023",
}

CERTIFICATIONS = [
    "Certified Core Python Developer -- Quality Thoughts, Chennai",
    "Certified Data Science with AI Engineer -- Quality Thoughts, Chennai",
    "National Workshop on Smart Emulation of IoT Projects -- RUSA 2.0, Tamil Nadu",
    "Internship in Python -- Brainary Spot Technology, Coimbatore",
]

# ---------------------------------------------------------------------------
# Search index -- flatten skills/projects/experience into retrievable chunks
# ---------------------------------------------------------------------------


def _build_index():
    chunks = []
    for project in PROJECTS:
        text = f"{project['title']} {project['description']} {' '.join(project['tags'])}"
        chunks.append({
            "source": "project",
            "title": project["title"],
            "snippet": project["description"],
            "tags": project["tags"],
            "text": text.lower(),
        })
    for skill in SKILLS:
        text = f"{skill['category']} {' '.join(skill['items'])}"
        chunks.append({
            "source": "skill",
            "title": skill["category"],
            "snippet": ", ".join(skill["items"]),
            "tags": skill["items"],
            "text": text.lower(),
        })
    for job in EXPERIENCE:
        text = f"{job['role']} {job['org']} {' '.join(job['points'])}"
        chunks.append({
            "source": "experience",
            "title": f"{job['role']} -- {job['org']}",
            "snippet": " ".join(job["points"]),
            "tags": [job["dates"]],
            "text": text.lower(),
        })
    return chunks


SEARCH_INDEX = _build_index()


def retrieve(query, top_k=4):
    """Very small keyword-overlap retriever -- ranks chunks by how many
    query terms they contain, weighted slightly toward tag matches."""
    terms = [t for t in re.split(r"[^a-z0-9+#]+", query.lower()) if t]
    if not terms:
        return []

    scored = []
    for chunk in SEARCH_INDEX:
        score = 0
        for term in terms:
            score += chunk["text"].count(term)
            if any(term in tag.lower() for tag in chunk["tags"]):
                score += 1
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    max_score = scored[0][0] if scored else 1

    results = []
    for score, chunk in scored[:top_k]:
        results.append({
            "source": chunk["source"],
            "title": chunk["title"],
            "snippet": chunk["snippet"],
            "tags": chunk["tags"],
            "relevance": round(min(score / max_score, 1.0), 2),
        })
    return results


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def home():
    return render_template(
        "index.html",
        profile=PROFILE,
        skills=SKILLS,
        projects=PROJECTS,
        experience=EXPERIENCE,
        education=EDUCATION,
        certifications=CERTIFICATIONS,
        year=datetime.now().year,
    )


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"query": query, "results": []})
    results = retrieve(query)
    return jsonify({"query": query, "results": results})


@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"status": "error", "message": "All fields are required."}), 400

    entry = {
        "name": name,
        "email": email,
        "message": message,
        "received_at": datetime.now().isoformat(timespec="seconds"),
    }

    existing = []
    if CONTACT_LOG.exists():
        try:
            existing = json.loads(CONTACT_LOG.read_text())
        except json.JSONDecodeError:
            existing = []
    existing.append(entry)
    CONTACT_LOG.write_text(json.dumps(existing, indent=2))

    return jsonify({"status": "ok", "message": "Thanks -- your message has been received."})


if __name__ == "__main__":
    app.run(debug=True)
