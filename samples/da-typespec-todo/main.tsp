import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";
import "./actions.tsp";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Agents;
using TypeSpec.M365.Copilot.Actions;

@agent(
  "Tasks Agent",
  "A declarative agent that helps you manage your tasks using the Microsoft Graph API",
)
@instructions(""" 
    Your role is to help users manage their tasks using the Microsoft Graph API. 

    ### Your responsibilities include:
    - **Task Management**:
      - Create tasks
      - Get tasks
      - Get task lists

    ### Skills:
    - When a user asks for all their tasks, you should be able to retrieve all task lists and then all their tasks.
  """)

@conversationStarter(#{ 
  title: "Important", 
  text: "Tell me all tasks that are important" 
})
@conversationStarter(#{ 
  title: "Urgent", 
  text: "Tell me all tasks that are overdue" 
})
@conversationStarter(#{ 
  title: "Prioritize", 
  text: "Based on all my tasks, what are the top 3 most important ones?" 
})

namespace TasksAgent {  
  @service
  @server(global.TaskAPI.SERVER_URL)
  @actions(global.TaskAPI.ACTIONS_METADATA)
  @useAuth(global.TaskAPI.TasksAgentAuth)
  namespace GitHubAPIActions {
    op getLists is global.TaskAPI.GetLists;
    op getTasks is global.TaskAPI.GetTasks;
    op createTask is global.TaskAPI.CreateTask;
  }
}