import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./prompts/instructions.tsp";
import "./env.tsp";

using TypeSpec.M365.Copilot.Agents;

@agent(
  "Azure DevOps Wiki Assistant",
  "Answers workplace and IT how-to questions from your organization's Azure DevOps Wiki (how-to guides, documentation, and knowledge-base pages). It searches the indexed wiki, preserves the guide's steps and tables, cites the source page, and clearly says when an answer isn't in the wiki."
)
@instructions(Prompts.INSTRUCTIONS)
@conversationStarter(#{
  title: "Request SharePoint access",
  text: "How do I request access to a SharePoint site, and what access levels are there?",
})
@conversationStarter(#{
  title: "Submit an IT ticket",
  text: "How do I submit an IT support ticket, and which priority should I use?",
})
@conversationStarter(#{
  title: "Onboard a new starter",
  text: "What is the onboarding checklist for a new starter?",
})
@conversationStarter(#{
  title: "Request time off",
  text: "How do I request time off, and what leave types are available?",
})
@conversationStarter(#{
  title: "Book a meeting room",
  text: "How do I book a meeting room in Outlook?",
})
namespace adowiki {
  // The ONLY knowledge source: the Azure DevOps Wiki Copilot connector.
  // connectionId is backslash-escaped because TypeSpec parses ${...} as interpolation;
  // the emitter outputs the literal token ${{ADO_WIKI_CONNECTION_ID}}, which the Agents
  // Toolkit substitutes from env/.env.<env> when the app package is built.
  op copilotConnectors is AgentCapabilities.CopilotConnectors<Connections = [
    {
      connectionId: "\${{ADO_WIKI_CONNECTION_ID}}";
    }
  ]>;
}
