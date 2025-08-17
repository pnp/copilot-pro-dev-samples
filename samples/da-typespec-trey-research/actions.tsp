import "@typespec/http";
import "@microsoft/typespec-m365-copilot";
import "./server-config.tsp";


using TypeSpec.Http;
using TypeSpec.M365.Copilot.Actions;

@service
@server(SERVER_URL)
@actions(TreyAPI.ACTIONS_METADATA)
namespace TreyAPI{
  /**
   * The base URL for the API - exported from server-config.tsp
   */
  const SERVER_URL = global.SERVER_URL;

  /**
   * Metadata for the API actions.
   */
  const ACTIONS_METADATA = #{
    nameForHuman: "Trey Research Agent",
    descriptionForHuman: "You are a handy assistant for consultants at Trey Research, a boutique consultancy specializing in software development and clinical trials.",
    descriptionForModel: "You are a handy assistant for consultants at Trey Research, a boutique consultancy specializing in software development and clinical trials.",
    legalInfoUrl: "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service",
    privacyPolicyUrl: "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement"
  };

  /**
 * Retrieve the consultant profile for the logged-in user including skills, roles, certifications, location, availability, and project assignments.
 */
  @route("/me")
  @card( #{ dataPath: "$.results",  title: "$.name", url:"$.consultantPhotoUrl", file: "cards/getUserInformation.json"}) 
  @get op getUserInformation(): Consultant;
 /**
 * Charge time to a specific project on behalf of the logged in user, and return the number of hours remaining in their forecast.
 */
  @route("/me/chargeTime")
  @card( #{ dataPath: "$",  title: "$.results.clientName", file: "cards/postBillhours.json"}) 
  @post op postBillhours(projectName:string, hours: integer): BillHoursResponse;
 /**
 * Get consultants working at Trey Research based on consultant name, project name, certifications, skills, roles and hours available. Returns detailed information about consultants identified from filters like name of the consultant, name of project, certifications, skills, roles and hours available. Multiple filters can be used in combination to refine the list of consultants returned
 */
  @route("/consultants")
  @card( #{ dataPath: "$.results",  title: "$.name", url:"$.consultantPhotoUrl", file: "cards/getConsultants.json"}) 
  @get  op getConsultants(): Consultant[];

  /* model definitions*/
  model Location {
    street: string;
    city: string;
    state: string;
    country: string;
    postalCode: string;
    latitude: float64;
    longitude: float64;
  }
  
  model Project {
    projectName: string;
    projectDescription: string;
    projectLocation: Location;
    mapUrl: url;
    role: string;
    forecastThisMonth: int32;
    forecastNextMonth: int32;
    deliveredLastMonth: int32;
    deliveredThisMonth: int32;
  }

  model BillHoursResult {
    status: int32;
    clientName: string;
    projectName: string;
    remainingForecast: int32;
    message: string;
  }

  model BillHoursResponse {
    results: BillHoursResult;
  }

  model Consultant {
    id: string;
    name: string;
    @format("email")
    email: string;
    phone: string;
    location: Location;
    skills: string[];
    certifications: string[];
    roles: string[];
    @format("uri")
    consultantPhotoUrl: string;
    projects: Project[];
    forecastThisMonth: int32;
    forecastNextMonth: int32;
    deliveredLastMonth: int32;
    deliveredThisMonth: int32;
  }
   
}