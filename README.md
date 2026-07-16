# Venkadesan Marimuthu — Portfolio

A single-page portfolio with a Flask backend. All content (skills, projects,
experience) lives in `app.py` as plain Python data, rendered into the page
with Jinja — edit it there and the page updates everywhere.

Two small pieces of real backend logic:

- **`POST /api/search`** — a lightweight keyword-retrieval engine that scores
  the portfolio's own content against a visitor's query and returns ranked
  results. This powers the "Query the Index" search box on the page.
- **`POST /api/contact`** — validates the contact form and appends messages
  to `contact_messages.json` (created on first submission).

## Run it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Project structure

```
portfolio/
├── app.py                  # Flask app: routes, data, search logic
├── requirements.txt
├── templates/
│   └── index.html          # Jinja template for the page
├── static/
│   ├── css/style.css       # Design system + layout
│   └── js/script.js        # Search box + contact form (fetch calls)
└── contact_messages.json   # Created automatically after first contact submission
```

## Editing your content

Open `app.py` and edit the `PROFILE`, `SKILLS`, `PROJECTS`, `EXPERIENCE`,
`EDUCATION`, and `CERTIFICATIONS` variables near the top. No HTML editing
needed for content changes — the template loops over these automatically.

## Deploying

This is a standard Flask app, so it deploys to any Python host (Render,
Railway, PythonAnywhere, a VPS with gunicorn, etc.). For production, run it
behind a real WSGI server instead of `app.run(debug=True)`, e.g.:

```bash
pip install gunicorn
gunicorn app:app
```
