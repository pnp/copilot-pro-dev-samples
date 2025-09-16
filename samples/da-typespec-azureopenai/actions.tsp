import "@typespec/http";
import "@microsoft/typespec-m365-copilot";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(AzureOpenAPI.SERVER_URL)
@actions(AzureOpenAPI.ACTIONS_METADATA)

namespace AzureOpenAPI {
  /**
   * Metadata for the AzureOpenAPI API actions.
   */
  const ACTIONS_METADATA = #{
    nameForHuman: "AzureOpenAPI",
    descriptionForHuman: "Query AzureOpenAPI.",
    descriptionForModel: "Query AzureOpenAPI.",
  };
  
  /**
   * The base URL for the AzureOpenAPI API.
   */
  const SERVER_URL = "<SERVER_URL>";
  const MODEL = "gpt-4o";
  const TEMPERATURE = 0.7;
  const TOP_P = 0.95;
  const MAX_TOKENS = 1024;
  const PRESENCE_PENALTY = 0.0;
  const FREQUENCY_PENALTY = 0.0;

  @doc("Searches for volunteering opportunities using Azure Open API")
  @useAuth(ApiKeyAuth<ApiKeyLocation.header, "api-key">)
  @route("/openai/deployments/${MODEL}/chat/completions")
  @post
  
  op searchVolunteerOpportunities(
    @body post: ChatCompletionsRequest,
    @query("api-version") apiVersion: string = "2025-01-01-preview",
  ): ChatCompletionsResponse;

  model ChatCompletionsRequest { 
    messages: Message[];
    temperature?: float32 = TEMPERATURE;
    top_p?: float32 = TOP_P;
    max_tokens?: int32 = MAX_TOKENS;
    n?: int32 = 1;
    stop?: string[];
    presence_penalty?: float32 = PRESENCE_PENALTY;
    frequency_penalty?: float32 = FREQUENCY_PENALTY;
  }
 
  model Message {
    role: "system" | "user" | "assistant";
    content: Content[];
  }

  model Content {
    type: "text";
    text: string
  }

  model ChatCompletionsResponse {
    id: string;
    choices: Choice[];
    usage: Usage;
  }

  model Choice {
    text: string;
    finish_reason: string;
  }

  model Usage {
    prompt_tokens: int32;
    completion_tokens: int32;
    total_tokens: int32;
  }

  model ErrorResponse {
    message?: string
  }
}
