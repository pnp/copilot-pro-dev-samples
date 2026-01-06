// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

const { app } = require("@azure/functions");

// Returns a list of available learning resources from JSON data
async function learningResources(req, context) {
  const resources = require("../learningResourcesData.json");
  const res = {
    status: 200,
    jsonBody: {
      results: resources,
    },
  };
  return res;
}

// Generates an interactive HTML quiz based on the requested topic
async function interactiveLearning(req, context) {
  const topic = req.query.get("topic") || "Node.js";
  const topicLower = topic.toLowerCase();
  let quizKey = "nodejs";
  if (topicLower.includes("node")) {
    quizKey = "nodejs";
  } else if (topicLower.includes("javascript")) {
    quizKey = "javascript";
  } else if (topicLower.includes("git")) {
    quizKey = "git";
  }
  const quizData = {
    nodejs: {
      title: "Node.js Basics Quiz",
      color: "#68a063",
      questions: [
        {
          question: "What is Node.js?",
          options: ["A JavaScript framework", "A JavaScript runtime", "A programming language", "A database"],
          correct: 1,
          explanation: "Node.js is a JavaScript runtime built on Chrome's V8 JavaScript engine"
        },
        {
          question: "Which command is used to install packages in Node.js?",
          options: ["node install", "npm install", "install package", "get package"],
          correct: 1,
          explanation: "npm install (or npm i) is used to install packages from the npm registry"
        },
        {
          question: "What does 'require()' do in Node.js?",
          options: ["Starts the server", "Imports modules", "Declares variables", "Exports functions"],
          correct: 1,
          explanation: "require() is used to import modules in Node.js (CommonJS syntax)"
        }
      ],
      keyPoints: [
        "Node.js allows JavaScript to run on the server",
        "npm is the default package manager for Node.js",
        "Use require() or import to load modules",
        "Node.js is event-driven and non-blocking"
      ]
    },
    javascript: {
      title: "JavaScript Fundamentals Quiz",
      color: "#f7df1e",
      questions: [
        {
          question: "Which keyword is used to declare a constant in JavaScript?",
          options: ["var", "let", "const", "constant"],
          correct: 2,
          explanation: "'const' declares a constant (read-only) variable in JavaScript"
        },
        {
          question: "What is the output of 'typeof null' in JavaScript?",
          options: ["'null'", "'undefined'", "'object'", "'number'"],
          correct: 2,
          explanation: "This is a known JavaScript quirk - typeof null returns 'object'"
        },
        {
          question: "Which method adds an element to the end of an array?",
          options: ["add()", "append()", "push()", "insert()"],
          correct: 2,
          explanation: "push() adds one or more elements to the end of an array"
        }
      ],
      keyPoints: [
        "Use 'let' and 'const' instead of 'var' in modern JavaScript",
        "JavaScript is single-threaded with asynchronous capabilities",
        "Arrow functions provide concise syntax",
        "Understand the difference between '==' and '==='"
      ]
    },
    git: {
      title: "Git Version Control Quiz",
      color: "#f05032",
      questions: [
        {
          question: "Which command stages all changes for commit?",
          options: ["git stage .", "git add .", "git commit .", "git push ."],
          correct: 1,
          explanation: "'git add .' stages all changes in the current directory"
        },
        {
          question: "What does 'git pull' do?",
          options: ["Uploads changes", "Downloads and merges changes", "Creates a branch", "Deletes remote branch"],
          correct: 1,
          explanation: "'git pull' fetches changes from remote and merges them into current branch"
        },
        {
          question: "Which command shows commit history?",
          options: ["git status", "git log", "git history", "git show"],
          correct: 1,
          explanation: "'git log' displays the commit history for the repository"
        }
      ],
      keyPoints: [
        "Always pull before starting new work",
        "Write meaningful commit messages",
        "Use branches for features and fixes",
        "Regularly push your work to remote"
      ]
    }
  };
  const quiz = quizData[quizKey];
  const fs = require('fs');
  const path = require('path');
  const templatePath = path.join(__dirname, '..', 'Pages', 'quiz-template.html');
  let html = fs.readFileSync(templatePath, 'utf8');
  const questionsHtml = quiz.questions.map((q, index) => `
    <div class="question-container ${index === 0 ? 'active' : ''}" data-question="${index}">
      <div class="question-number">Question ${index + 1} of ${quiz.questions.length}</div>
      <div class="question">${q.question}</div>
      <div class="options">
        ${q.options.map((opt, optIndex) => `
          <div class="option" data-option="${optIndex}">${opt}</div>
        `).join('')}
      </div>
      <div class="feedback" id="feedback-${index}">
        <strong></strong>
        <p>${q.explanation}</p>
      </div>
      <div class="buttons">
        <button class="next-btn" id="next-${index}" disabled>
          ${index === quiz.questions.length - 1 ? 'Show Results' : 'Next Question →'}
        </button>
      </div>
    </div>
  `).join('');
  const keyPointsHtml = quiz.keyPoints.map(point => `<li>${point}</li>`).join('');
  html = html.replace(/\{\{TITLE\}\}/g, quiz.title);
  html = html.replace(/\{\{COLOR\}\}/g, quiz.color);
  html = html.replace(/\{\{QUESTION_COUNT\}\}/g, quiz.questions.length);
  html = html.replace('{{QUESTIONS}}', questionsHtml);
  html = html.replace('{{KEY_POINTS}}', keyPointsHtml);
  html = html.replace('{{QUIZ_DATA}}', JSON.stringify(quiz.questions));
  return {
    status: 200,
    headers: { "Content-Type": "text/html" },
    body: html
  };
}

app.http("learningResources", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: learningResources,
});

app.http("interactiveLearning", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: interactiveLearning,
});
