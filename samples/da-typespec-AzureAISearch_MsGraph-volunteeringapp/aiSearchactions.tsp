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
    descriptionForModel: "Helps users find info about volunteering opportunities using Azure AI Search.",
    legalInfoUrl: "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service",
    privacyPolicyUrl: "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement"
  };

  const SERVER_URL = "https://aivolunteering.search.windows.net";
  
  @doc("Searches for volunteering opportunities using Azure AI Search.")
  @post
  @useAuth(ApiKeyAuth<ApiKeyLocation.header, "api-key">)
  @route("/indexes/vol/docs/search")
  @card(#{ dataPath: "$.value", title: "$.title", url: "$.chunk", file: "adaptiveCards/searchResults.json" })
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