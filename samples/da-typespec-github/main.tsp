import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./actions.tsp";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Agents;
using TypeSpec.M365.Copilot.Actions;

@agent(
  "GitHub Issues Agent",
  "GitHub Issues Agent for Microsoft 365 Copilot"
)

@instructions(""" 
    You are an expert at helping users find issues in GitHub repositories and answering questions related to them from other data in Microsoft 365.
  
    Guidelines:
  
    * Every time a user talks about issues, always refer to them as GitHub issues.
    * If you don't have information to share, do not hallucinate.
  """)

@conversationStarter(#{
  title: "Best practices",
  text: "What are some best practices in issue management using GitHub?",
})
@conversationStarter(#{
  title: "Top issues",
  text: "What are the current top issues assigned to",
})
@conversationStarter(#{
  title: "Latest 5 issues",
  text: "List the latest 5 issues from the repo",
})
@conversationStarter(#{
  title: "Issue prioritization",
  text: "Based on the latest issues, which one should we prioritize?",
})
@conversationStarter(#{
  title: "Issues visualizations",
  text: "Visualize the data as a pie chart grouped by assignee based on the the latest issues.",
})
@conversationStarter(#{
  title: "Issues by theme",
  text: "Search issues with the theme",
})

namespace GitHubIssuesAgent {  
  /** 
   * Enable WebSearch capabilities for the agent.
   */
  op webSearch is AgentCapabilities.WebSearch<TSites = [
    {
      url: "https://docs.github.com/en/issues";
    }
  ]>;

  /**
   * Enable Code Interpreter capabilities for the agent.
   */
  op codeInterpreter is AgentCapabilities.CodeInterpreter;

  // The agent will use the GitHub API to search for issues.
  @service
  @server(global.GitHubAPI.SERVER_URL)
  @actions(global.GitHubAPI.ACTIONS_METADATA)
  namespace GitHubAPIActions {
    op searchIssues is global.GitHubAPI.searchIssues;
  }
}