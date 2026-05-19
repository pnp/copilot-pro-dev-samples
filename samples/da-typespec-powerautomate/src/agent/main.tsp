import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./actions/invokePAFlow.tsp";
import "./prompts/instructions.tsp";
import "./env.tsp";

using TypeSpec.M365.Copilot.Agents;

@agent(
  "InvokePowerAutomate",
  "Declarative agent created with Microsoft 365 Agents Toolkit and TypeSpec for Microsoft 365 Copilot."
)
@instructions(Prompts.INSTRUCTIONS)
// Uncomment this part to add a conversation starter to the agent.
// This will be shown to the user when the agent is first created.
// @conversationStarter(#{
//   title: "Get latest issues",
//   text: "Get the latest issues from GitHub" 
// })
namespace InvokePowerAutomate {  
  // Expose the Power Automate flow invocation action
  op invokePA is PowerAutomateAPI.sendEmail;
}