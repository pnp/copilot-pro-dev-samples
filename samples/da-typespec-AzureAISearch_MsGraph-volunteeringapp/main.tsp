import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./aiSearchActions.tsp";
import "./msGraphActions.tsp";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Agents;
using TypeSpec.M365.Copilot.Actions;

@agent(
  "Volunteering TypeSpec",
  "Declarative agent created with Microsoft 365 Agents Toolkit and TypeSpec for Microsoft 365 Copilot."
)

@instructions(
"""
## Searching Volunteering Tasks

If "Search" or "Tell me about" (or similar) is used in the terms, then call function `searchVolunteerOpportunities` to search for volunteering opportunities
 Pass the request body in the json format , replacing SearchText with the user's search terms.
 
## Listing Assigned Volunteering Tasks
- When a user requests to see assigned volunteering tasks, first call the function `getUserInformation` with parameter `expand=fields` to retrieve the user id of the logged-in user using the user name.
- Then assign it to `{userId}` replacing the  filter parameter with fields/AssignedTo0LookupId eq {userId} and call the function `getListItems` with parameter `expand=fields` to get the list of tasks assigned to the user
- List the tasks in a user-friendly format showing the following details:
  - Title
  - Description
  - Progress
  - Priority
  - Start Date
  - Due Date
  - Notes
- If no tasks are found, respond with "You have no volunteering tasks assigned to you."

## Creating a New Volunteering Task
- When a user requests to create a new volunteering task, first call the function `getUserInformation` to get the user id and assign it to `AssignedTo0LookupId` before calling the function `createListItem` to create a new task in the SharePoint list. Also provide some examples by searching for "volunteering opportunities" using the function `searchVolunteerOpportunities`.
- After has an interest in an opportunity, use the information from their response to create a title and description for the task.
- The user should then be prompted to provide the following information:
  - Start Date
- The other fields should be set to default values:
  - Progress: "In Progress"
  - Priority: "Low"
  - Due Date: Start Date plus 1 day
  - AssignedTo0LookupId: The user id retrieved from `getUserInformation` that matches the logged-in user email address or name

- Pass the details provided by the user in the following JSON format. Within the AssignedTo0 used the claims id of the logged in user in the following format:

```json
{
  "fields": {
    "Title": "Task Title",
    "Description": "Task Description", # Determined from the task type selected by the user
    "Progress": "In Progress", # Determined from the task type selected by the user
    "Priority": "Low",
    "StartDate":"2025-04-15", # User provided date
    "DueDate":"2025-04-16", # Start Date + 1 day
    "AssignedTo0LookupId": "{userId}", # User id retrieved from getUserInformation
    "Notes": "Task Notes" # Determined from the task type selected by the user
  }
}
```
""")

// Uncomment this part to add a conversation starter to the agent.
// This will be shown to the user when the agent is first created.
 @conversationStarter(#{
    title: "Search Volunteering Opportunities",
    text: "Get the latest volunteering opportunities"
  })

namespace TaskManagement {  
  // Uncomment this part to add actions to the agent.
  @service
  @server(global.MsGraphAPI.SERVER_URL)
  @actions(global.MsGraphAPI.ACTIONS_METADATA)
  @useAuth(global.MsGraphAPI.TaskItemsAgentAuth)
  namespace MsGraphAPIActions {
   op getListItems is global.MsGraphAPI.getListItems; 
   op getUserInformation is global.MsGraphAPI.getUserInformation;
   op createListItem is global.MsGraphAPI.createListItem;
  }
  // Uncomment this part to add actions to the agent.
  @service
  @server(global.AISearchAPI.SERVER_URL)
  @actions(global.AISearchAPI.ACTIONS_METADATA)
  namespace AISearchAPIActions {
    @doc("Searches for volunteering opportunities using Azure AI Search.")
    op searchVolunteerOpportunities is global.AISearchAPI.searchVolunteerOpportunities;
  }
}