import "@typespec/http";
import "@microsoft/typespec-m365-copilot";

using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(Environment.PA_APP_SERVER_URL)
@actions(PowerAutomateAPI.ACTIONS_METADATA)
@useAuth(PowerAutomateAPI.PAAgentAuth)
 
namespace PowerAutomateAPI {
  const ACTIONS_METADATA = #{
    nameForHuman: "Invoke PA Flow",
    descriptionForHuman: "Invoke a Power Automate flow.",
    descriptionForModel: "Invoke a Power Automate flow.",
  };
 
  /**
   * The invoke path for the Power Automate flow.
   */
  const FLOW_URL = Environment.PA_APP_INVOKE_PATH;

  /**
   * Invoke a Power Automate flow
   * @param body The flow parameters as JSON string
   */
  @route(FLOW_URL)
  @post op sendEmail(
    @query("api-version") apiVersion: string = "1",
    @doc("The EmailData model containing the email body, recipient email address, and subject to be sent via Power Automate.")
      @body request: EmailData
  ): {
    @statusCode statusCode: 200;
    @body response: string;
  } | {
    @statusCode statusCode: 400;
    @doc("Bad request: the flow invocation request was invalid or missing required fields.")
    @body error: string;
  } | {
    @statusCode statusCode: 500;
    @doc("Server error: an unexpected error occurred while invoking the Power Automate flow.")
    @body error: string;
  };
  
   model EmailData {

      @doc("The details of the email body")
      @example("Latest volunteering opportunities")
      body: string;

      @doc("The current user email address")
      @example("test@test.onmicrosoft.com")
      email: string;

      @doc("The subject of the email")
      @example("Latest volunteering opportunities")
      subject: string;
  }
  
  model PAAgentAuth is OAuth2Auth<[{
    type: OAuth2FlowType.authorizationCode;
    authorizationUrl: "https://login.microsoftonline.com/<tenantid>/oauth2/v2.0/authorize";
    tokenUrl: "https://login.microsoftonline.com/<tenantid>/oauth2/v2.0/token";
    refreshUrl: "https://login.microsoftonline.com/<tenantid>/oauth2/v2.0/refresh";
    scopes: ["https://service.flow.microsoft.com//.default"];
  }]> { }

}