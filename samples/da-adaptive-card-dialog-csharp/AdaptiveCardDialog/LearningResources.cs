// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using System.Net;
using System.Text;
using System.Text.Json;

namespace AdaptiveCardDialog
{
    public class LearningResources
    {
        private readonly ILogger _logger;
        private static readonly string _htmlTemplate;

        static LearningResources()
        {
            var templatePath = Path.Combine(AppContext.BaseDirectory, "Pages", "quiz-template.html");
            _htmlTemplate = File.ReadAllText(templatePath);
        }

        public LearningResources(ILoggerFactory loggerFactory)
        {
            _logger = loggerFactory.CreateLogger<LearningResources>();
        }

        // Returns a list of available learning resources from data
        [Function("learningResources")]
        public async Task<HttpResponseData> GetLearningResourcesAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a learningResources request.");

            var resources = LearningResourceData.GetResources();
            var response = req.CreateResponse(HttpStatusCode.OK);
            await response.WriteAsJsonAsync(new { results = resources });
            return response;
        }

        // Generates an interactive HTML quiz based on the requested topic
        [Function("interactiveLearning")]
        public async Task<HttpResponseData> GetInteractiveLearningAsync(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get")] HttpRequestData req)
        {
            _logger.LogInformation("C# HTTP trigger function processed an interactiveLearning request.");

            string topic = req.Query["topic"] ?? "Node.js";
            string topicLower = topic.ToLowerInvariant();

            string quizKey = "nodejs";
            if (topicLower.Contains("node"))
                quizKey = "nodejs";
            else if (topicLower.Contains("javascript"))
                quizKey = "javascript";
            else if (topicLower.Contains("git"))
                quizKey = "git";

            var quizData = GetQuizData();
            if (!quizData.TryGetValue(quizKey, out var quiz))
                quiz = quizData["nodejs"];

            string html = BuildQuizHtml(quiz);

            var response = req.CreateResponse(HttpStatusCode.OK);
            response.Headers.Add("Content-Type", "text/html; charset=utf-8");
            byte[] bytes = Encoding.UTF8.GetBytes(html);
            await response.Body.WriteAsync(bytes);
            return response;
        }

        private static string BuildQuizHtml(QuizModel quiz)
        {
            var sb = new StringBuilder();
            for (int i = 0; i < quiz.Questions.Count; i++)
            {
                var q = quiz.Questions[i];
                string activeClass = i == 0 ? "active" : "";
                string btnLabel = i == quiz.Questions.Count - 1 ? "Show Results" : "Next Question →";
                string optionsHtml = string.Join("\n        ",
                    q.Options.Select((opt, optIndex) =>
                        $"<div class=\"option\" data-option=\"{optIndex}\">{EscapeHtml(opt)}</div>"));

                sb.AppendLine($@"    <div class=""question-container {activeClass}"" data-question=""{i}"">
      <div class=""question-number"">Question {i + 1} of {quiz.Questions.Count}</div>
      <div class=""question"">{EscapeHtml(q.Question)}</div>
      <div class=""options"">
        {optionsHtml}
      </div>
      <div class=""feedback"" id=""feedback-{i}"">
        <strong></strong>
        <p>{EscapeHtml(q.Explanation)}</p>
      </div>
      <div class=""buttons"">
        <button class=""next-btn"" id=""next-{i}"" disabled>
          {btnLabel}
        </button>
      </div>
    </div>");
            }

            string questionsHtml = sb.ToString();
            string keyPointsHtml = string.Join("\n            ",
                quiz.KeyPoints.Select(p => $"<li>{EscapeHtml(p)}</li>"));

            var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
            string quizDataJson = JsonSerializer.Serialize(quiz.Questions, jsonOptions);

            string html = _htmlTemplate;
            html = html.Replace("{{TITLE}}", EscapeHtml(quiz.Title));
            html = html.Replace("{{COLOR}}", quiz.Color);
            html = html.Replace("{{QUESTION_COUNT}}", quiz.Questions.Count.ToString());
            html = html.Replace("{{QUESTIONS}}", questionsHtml);
            html = html.Replace("{{KEY_POINTS}}", keyPointsHtml);
            html = html.Replace("{{QUIZ_DATA}}", quizDataJson);
            return html;
        }

        private static string EscapeHtml(string input)
        {
            if (input == null) return string.Empty;
            return System.Net.WebUtility.HtmlEncode(input);
        }

        private static Dictionary<string, QuizModel> GetQuizData()
        {
            return new Dictionary<string, QuizModel>
            {
                ["nodejs"] = new QuizModel
                {
                    Title = "Node.js Basics Quiz",
                    Color = "#68a063",
                    Questions = new List<QuizQuestion>
                    {
                        new() {
                            Question = "What is Node.js?",
                            Options = new List<string> { "A JavaScript framework", "A JavaScript runtime", "A programming language", "A database" },
                            Correct = 1,
                            Explanation = "Node.js is a JavaScript runtime built on Chrome's V8 JavaScript engine"
                        },
                        new() {
                            Question = "Which command is used to install packages in Node.js?",
                            Options = new List<string> { "node install", "npm install", "install package", "get package" },
                            Correct = 1,
                            Explanation = "npm install (or npm i) is used to install packages from the npm registry"
                        },
                        new() {
                            Question = "What does 'require()' do in Node.js?",
                            Options = new List<string> { "Starts the server", "Imports modules", "Declares variables", "Exports functions" },
                            Correct = 1,
                            Explanation = "require() is used to import modules in Node.js (CommonJS syntax)"
                        }
                    },
                    KeyPoints = new List<string>
                    {
                        "Node.js allows JavaScript to run on the server",
                        "npm is the default package manager for Node.js",
                        "Use require() or import to load modules",
                        "Node.js is event-driven and non-blocking"
                    }
                },
                ["javascript"] = new QuizModel
                {
                    Title = "JavaScript Fundamentals Quiz",
                    Color = "#f7df1e",
                    Questions = new List<QuizQuestion>
                    {
                        new() {
                            Question = "Which keyword is used to declare a constant in JavaScript?",
                            Options = new List<string> { "var", "let", "const", "constant" },
                            Correct = 2,
                            Explanation = "'const' declares a constant (read-only) variable in JavaScript"
                        },
                        new() {
                            Question = "What is the output of 'typeof null' in JavaScript?",
                            Options = new List<string> { "'null'", "'undefined'", "'object'", "'number'" },
                            Correct = 2,
                            Explanation = "This is a known JavaScript quirk - typeof null returns 'object'"
                        },
                        new() {
                            Question = "Which method adds an element to the end of an array?",
                            Options = new List<string> { "add()", "append()", "push()", "insert()" },
                            Correct = 2,
                            Explanation = "push() adds one or more elements to the end of an array"
                        }
                    },
                    KeyPoints = new List<string>
                    {
                        "Use 'let' and 'const' instead of 'var' in modern JavaScript",
                        "JavaScript is single-threaded with asynchronous capabilities",
                        "Arrow functions provide concise syntax",
                        "Understand the difference between '==' and '==='"
                    }
                },
                ["git"] = new QuizModel
                {
                    Title = "Git Version Control Quiz",
                    Color = "#f05032",
                    Questions = new List<QuizQuestion>
                    {
                        new() {
                            Question = "Which command stages all changes for commit?",
                            Options = new List<string> { "git stage .", "git add .", "git commit .", "git push ." },
                            Correct = 1,
                            Explanation = "'git add .' stages all changes in the current directory"
                        },
                        new() {
                            Question = "What does 'git pull' do?",
                            Options = new List<string> { "Uploads changes", "Downloads and merges changes", "Creates a branch", "Deletes remote branch" },
                            Correct = 1,
                            Explanation = "'git pull' fetches changes from remote and merges them into current branch"
                        },
                        new() {
                            Question = "Which command shows commit history?",
                            Options = new List<string> { "git status", "git log", "git history", "git show" },
                            Correct = 1,
                            Explanation = "'git log' displays the commit history for the repository"
                        }
                    },
                    KeyPoints = new List<string>
                    {
                        "Always pull before starting new work",
                        "Write meaningful commit messages",
                        "Use branches for features and fixes",
                        "Regularly push your work to remote"
                    }
                }
            };
        }
    }

    internal class QuizModel
    {
        public string Title { get; set; } = string.Empty;
        public string Color { get; set; } = string.Empty;
        public List<QuizQuestion> Questions { get; set; } = new();
        public List<string> KeyPoints { get; set; } = new();
    }

    internal class QuizQuestion
    {
        public string Question { get; set; } = string.Empty;
        public List<string> Options { get; set; } = new();
        public int Correct { get; set; }
        public string Explanation { get; set; } = string.Empty;
    }
}
