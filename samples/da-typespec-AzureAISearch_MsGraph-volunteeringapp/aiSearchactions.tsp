import "@typespec/http";
import "@microsoft/typespec-m365-copilot";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(AISearchAPI.SERVER_URL)
@actions(AISearchAPI.ACTIONS_METADATA)
namespace AISearchAPI {
  const ACTIONS_METADATA = #{
    nameForHuman: "Volunteering Agent",
    descriptionForHuman: "Helps users find info about volunteering opportunities using Azure AI Search.",
    descriptionForModel: "Helps users find info about volunteering opportunities using Azure AI Search."
  };

  const SERVER_URL = "https://<AI_SEARCH_ENDPOINT>.search.windows.net";
  
  @doc("Searches for volunteering opportunities using Azure AI Search.")
  @post
  @useAuth(ApiKeyAuth<ApiKeyLocation.header, "api-key">)
  @route("/indexes/vol/docs/search")
  
  op searchVolunteerOpportunities(
    @body post: DataRequest,
    @query("api-version") apiVersion: string = "2025-05-01-preview",
  ): DataResponse;

  model DataRequest { 
  count: boolean;
  vectorQueries: [
    {
      kind: string = "text";
      text: string = "volunteering";
      fields: string = "contentVector";
    }
  ];
  }

  model DataResponse {
    "@search.answers": DataItem[];
  }

  model DataItem {    
    key: string;    
    text: string;   
    started: string;
    highlights: string;
    score: decimal128;
  }
}