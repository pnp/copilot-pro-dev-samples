import html as html_module
import json
import logging
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

DATA_FILE = Path(__file__).parent / "src" / "learningResourcesData.json"
TEMPLATE_FILE = Path(__file__).parent / "src" / "Pages" / "quiz-template.html"

try:
    _html_template = TEMPLATE_FILE.read_text(encoding="utf-8")
except Exception:
    logging.exception("Failed to load quiz HTML template")
    raise

QUIZ_DATA = {
    "nodejs": {
        "title": "Node.js Basics Quiz",
        "color": "#68a063",
        "questions": [
            {
                "question": "What is Node.js?",
                "options": ["A JavaScript framework", "A JavaScript runtime", "A programming language", "A database"],
                "correct": 1,
                "explanation": "Node.js is a JavaScript runtime built on Chrome's V8 JavaScript engine",
            },
            {
                "question": "Which command is used to install packages in Node.js?",
                "options": ["node install", "npm install", "install package", "get package"],
                "correct": 1,
                "explanation": "npm install (or npm i) is used to install packages from the npm registry",
            },
            {
                "question": "What does 'require()' do in Node.js?",
                "options": ["Starts the server", "Imports modules", "Declares variables", "Exports functions"],
                "correct": 1,
                "explanation": "require() is used to import modules in Node.js (CommonJS syntax)",
            },
        ],
        "keyPoints": [
            "Node.js allows JavaScript to run on the server",
            "npm is the default package manager for Node.js",
            "Use require() or import to load modules",
            "Node.js is event-driven and non-blocking",
        ],
    },
    "javascript": {
        "title": "JavaScript Fundamentals Quiz",
        "color": "#f7df1e",
        "questions": [
            {
                "question": "Which keyword is used to declare a constant in JavaScript?",
                "options": ["var", "let", "const", "constant"],
                "correct": 2,
                "explanation": "'const' declares a constant (read-only) variable in JavaScript",
            },
            {
                "question": "What is the output of 'typeof null' in JavaScript?",
                "options": ["'null'", "'undefined'", "'object'", "'number'"],
                "correct": 2,
                "explanation": "This is a known JavaScript quirk - typeof null returns 'object'",
            },
            {
                "question": "Which method adds an element to the end of an array?",
                "options": ["add()", "append()", "push()", "insert()"],
                "correct": 2,
                "explanation": "push() adds one or more elements to the end of an array",
            },
        ],
        "keyPoints": [
            "Use 'let' and 'const' instead of 'var' in modern JavaScript",
            "JavaScript is single-threaded with asynchronous capabilities",
            "Arrow functions provide concise syntax",
            "Understand the difference between '==' and '==='",
        ],
    },
    "git": {
        "title": "Git Version Control Quiz",
        "color": "#f05032",
        "questions": [
            {
                "question": "Which command stages all changes for commit?",
                "options": ["git stage .", "git add .", "git commit .", "git push ."],
                "correct": 1,
                "explanation": "'git add .' stages all changes in the current directory",
            },
            {
                "question": "What does 'git pull' do?",
                "options": ["Uploads changes", "Downloads and merges changes", "Creates a branch", "Deletes remote branch"],
                "correct": 1,
                "explanation": "'git pull' fetches changes from remote and merges them into current branch",
            },
            {
                "question": "Which command shows commit history?",
                "options": ["git status", "git log", "git history", "git show"],
                "correct": 1,
                "explanation": "'git log' displays the commit history for the repository",
            },
        ],
        "keyPoints": [
            "Always pull before starting new work",
            "Write meaningful commit messages",
            "Use branches for features and fixes",
            "Regularly push your work to remote",
        ],
    },
}


@app.route(route="learningResources", methods=["GET"])
def learning_resources(req: func.HttpRequest) -> func.HttpResponse:
    try:
        resources = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("Error reading learning resources data")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve learning resources"}),
            status_code=500,
            mimetype="application/json",
        )
    return func.HttpResponse(
        json.dumps({"results": resources}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="interactiveLearning", methods=["GET"])
def interactive_learning(req: func.HttpRequest) -> func.HttpResponse:
    if not _html_template:
        return func.HttpResponse(
            "<html><body><h2>Error: Quiz template unavailable.</h2></body></html>",
            status_code=500,
            mimetype="text/html",
        )

    topic = (req.params.get("topic") or "Node.js").strip()
    topic_lower = topic.lower()

    if "node" in topic_lower:
        quiz_key = "nodejs"
    elif "javascript" in topic_lower:
        quiz_key = "javascript"
    elif "git" in topic_lower:
        quiz_key = "git"
    else:
        quiz_key = "nodejs"

    quiz = QUIZ_DATA[quiz_key]
    total = len(quiz["questions"])

    questions_html_parts = []
    for index, q in enumerate(quiz["questions"]):
        options_html = "".join(
            f'<div class="option" data-option="{opt_index}">{html_module.escape(str(opt))}</div>'
            for opt_index, opt in enumerate(q["options"])
        )
        active_class = "active" if index == 0 else ""
        next_label = "Show Results" if index == total - 1 else "Next Question &rarr;"
        questions_html_parts.append(
            f'<div class="question-container {active_class}" data-question="{index}">'
            f'<div class="question-number">Question {index + 1} of {total}</div>'
            f'<div class="question">{html_module.escape(q["question"])}</div>'
            f'<div class="options">{options_html}</div>'
            f'<div class="feedback" id="feedback-{index}">'
            f'<strong></strong><p>{html_module.escape(q["explanation"])}</p></div>'
            f'<div class="buttons"><button class="next-btn" id="next-{index}" disabled>'
            f"{next_label}</button></div>"
            f"</div>"
        )

    key_points_html = "".join(
        f"<li>{html_module.escape(point)}</li>" for point in quiz["keyPoints"]
    )

    page = _html_template
    page = page.replace("{{TITLE}}", html_module.escape(quiz["title"]))
    page = page.replace("{{COLOR}}", quiz["color"])
    page = page.replace("{{QUESTION_COUNT}}", str(total))
    page = page.replace("{{QUESTIONS}}", "".join(questions_html_parts))
    page = page.replace("{{KEY_POINTS}}", key_points_html)
    page = page.replace("{{QUIZ_DATA}}", json.dumps(quiz["questions"]))

    return func.HttpResponse(
        page,
        status_code=200,
        mimetype="text/html",
    )