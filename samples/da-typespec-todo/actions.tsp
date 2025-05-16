import "@typespec/http";
import "@typespec/openapi3";
import "@microsoft/typespec-m365-copilot";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(TaskAPI.SERVER_URL)
@actions(TaskAPI.ACTIONS_METADATA)
namespace TaskAPI {
  /**
   * Metadata for the Microsoft Graph Tasks API actions.
   */
  const ACTIONS_METADATA = #{
    nameForHuman: "Tasks via Microsoft Graph API",
    descriptionForHuman: "Manage your tasks",
    descriptionForModel: "Manage all aspects of personal tasks using the Microsoft Graph API",
  };
  
  /**
   * The base URL for the Microsoft Graph API.
   */
  const SERVER_URL = "https://graph.microsoft.com/v1.0";

  /**
   * Get all todo lists
   */
  @route("/me/todo/lists")
  @get op GetLists(): string;

  /**
   * Get all tasks in a list
   * @param listId The ID of the list. If you don't know the 'id', use the GetLists operation to get the full details of the lists, including the 'id'.
   */
  @route("/me/todo/lists/{listId}/tasks")
  @get op GetTasks(listId: string): string;

  /**
   * Create a new task in a list
   * @param listId The ID of the list. If you don't know the 'id', use the GetLists operation to get the full details of the lists, including the 'id'.
   * @param task The task to create. The entire request body is the task object.
   * @returns The created task
   */
  @route("/me/todo/lists/{listId}/tasks")
  @post op CreateTask(listId: string, @body task: Task): string;

  model Task {
    /**
     * The ID of the task.
     */
    @visibility(Lifecycle.Read)
    id: string;
    /**
     * The title of the task.
     */
    title: string;

    /**
     * The importance of the task.
     */
    importance: "low" | "normal" | "high" = "normal";
  }

  model TasksAgentAuth is OAuth2Auth<[{
    type: OAuth2FlowType.authorizationCode;
    authorizationUrl: "https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize";
    tokenUrl: "https://login.microsoftonline.com/organizations/oauth2/v2.0/token";
    refreshUrl: "https://login.microsoftonline.com/organizations/oauth2/v2.0/token";
    scopes: ["Tasks.ReadWrite"];
  }]> { }
}