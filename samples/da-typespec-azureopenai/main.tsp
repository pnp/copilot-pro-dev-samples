import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./actions.tsp";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Agents;
using TypeSpec.M365.Copilot.Actions;

@agent(
  "OpenAITypeSpec",
  "Declarative agent created with Microsoft 365 Agents Toolkit and TypeSpec for Microsoft 365 Copilot."
)

@instructions("""
You can call the `searchVolunteerOpportunities` API to get a list of available volunteering opportunities. 

**Example API Request**

Here’s an example of the JSON payload sent to Azure OpenAI replacing <Prompt> with user prompt:

```json
{
  "messages": [
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are an helpful assistant helping to gather volunteering opportunities"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "<Prompt>"
        }
      ]
    }
  ],
  "temperature": 0.7,
  "top_p": 0.95,
  "max_tokens": 800
}
```
""")

// Uncomment this part to add a conversation starter to the agent.
// This will be shown to the user when the agent is first created.
// @conversationStarter(#{
//   title: "Get latest issues",
//   text: "Get the latest issues from GitHub" 
// })

namespace OpenAITypeSpec {  
  @service
  @server(global.AzureOpenAPI.SERVER_URL)
  @actions(global.AzureOpenAPI.ACTIONS_METADATA)
  namespace AzureOpenAPIActions {
    op searchVolunteerOpportunities is global.AzureOpenAPI.searchVolunteerOpportunities;
  }
}