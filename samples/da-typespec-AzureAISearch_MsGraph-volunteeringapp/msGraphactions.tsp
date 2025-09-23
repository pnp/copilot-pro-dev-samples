import "@typespec/http";
import "@microsoft/typespec-m365-copilot";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(MsGraphAPI.SERVER_URL)
@actions(MsGraphAPI.ACTIONS_METADATA)
namespace MsGraphAPI {
  const ACTIONS_METADATA = #{
    nameForHuman: "Volunteering Tracker",
    descriptionForHuman: "Helps users retrieve volunteering opportunities assigned to them.",
    descriptionForModel: "Helps users retrieve volunteering opportunities assigned to them.",
  };

  /**
   * The base URL for the Microsoft Graph API.
   */
  const SERVER_URL = "https://graph.microsoft.com/v1.0";  
  const SITE_ID = "reshmee.sharepoint.com,541d6ad1-322f-419d-8575-5309a29c3cf8,6b96c932-79a5-4f2a-91dc-41689290ebe7";
  const LIST_ID = "cb530b8f-5af3-44ad-8270-ec89d0357ae5";

  /**
   * Get all tasks in a list
   * @param filter The filter to apply to the list items.
   * @param expand The properties to expand in the response.
   */
  @route("/sites/${SITE_ID}/lists/${LIST_ID}/items")
  @get op getListItems(
    @query filter: string,
    @query expand?: string = "fields",
  ): ListItemsResponse;
  
  /**
   * Create a new item in the specified list.
   * @param input The fields for the new list item.
   */
  @route("/sites/${SITE_ID}/lists/${LIST_ID}/items")
  @post op createListItem(
    @body input: CreateListItemRequest
  ): CreateListItemResponse;
  
  /**
   * Get user information from the "User Information List"
   * @param siteId The ID of the site. If you don't know the 'id'
   */
  @route("/sites/${SITE_ID}/lists/User Information List/items")
  @get op getUserInformation(
    @query expand?: string = "fields",
    @header Prefer?: string
  ): UserInformationListResponse;

  model ListItemsResponse {
    @doc("Metadata context URL")
    "@odata.context": string;
    value: ListItem[];
  }

  model ListItem {
    id: string;
    createdDateTime: string;
    lastModifiedDateTime: string;
    webUrl: string;
    createdBy: CreatedBy;
    lastModifiedBy: CreatedBy;
    fields: ListItemFields;
  }

  model CreatedBy {
    user: UserInfo;
  }

  model UserInfo {
    email?: string;
    id?: string;
    displayName?: string;
  }

  model ListItemFields {
    Title?: string;
    Description?: string;
    Progress?: string;
    Priority?: string;
    StartDate?: string;
    DueDate?: string;
    AssignedTo0LookupId?: string;
    Created?: string;
    Modified?: string;
    AuthorLookupId?: string;
    EditorLookupId?: string;
    Attachments?: boolean;
    Notes?: string;
  }

  model CreateListItemRequest {
    fields: ListItemFields;
  }

  model CreateListItemResponse {
    id: string;
    fields: ListItemFields;
  }

  model UserInformationListResponse {
    "@odata.context": string;
    value: UserInformationListItem[];
  }

  model UserInformationListItem {
    id: string;
    createdDateTime: string;
    lastModifiedDateTime: string;
    webUrl: string;
    createdBy: SimpleUser;
    lastModifiedBy: SimpleUser;
    fields: UserInformationFields;
  }

  model SimpleUser {
    user: SimpleUserInfo;
  }

  model SimpleUserInfo {
    displayName?: string;
  }

  model UserInformationFields {
    id?: string;
    EMail?: string;
  }

  model TaskItemsAgentAuth is OAuth2Auth<[{
    type: OAuth2FlowType.authorizationCode;
    authorizationUrl: "https://login.microsoftonline.com/39f0e149-6ce0-483e-8acf-b6faa229a203/oauth2/v2.0/authorize";
    tokenUrl: "https://login.microsoftonline.com/39f0e149-6ce0-483e-8acf-b6faa229a203/oauth2/v2.0/token";
    refreshUrl: "https://login.microsoftonline.com/39f0e149-6ce0-483e-8acf-b6faa229a203/oauth2/v2.0/refresh";
    scopes: ["User.Read", "Directory.Read.All", "SharePoint.ReadWrite.All"];
  }]> { }

}