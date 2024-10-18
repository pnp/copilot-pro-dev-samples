import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import ProfilesApiService from "../services/snow_profiles"

/**
 * This function handles the HTTP request and returns the profile information.
 *
 * @param {HttpRequest} req - The HTTP request.
 * @param {InvocationContext} context - The Azure Functions context object.
 * @returns {Promise<Response>} - A promise that resolves with the HTTP response containing the profile information.
 */

export async function profiles(
    req: HttpRequest,
    context: InvocationContext
  ): Promise<HttpResponseInit> {
    
    // Initialize response.
    const res: HttpResponseInit = {
      status: 200,
      jsonBody: {
        results: [],
      },
    };
  
    try {
        // Get input parameters.
        //const email = req.query.get("email");
        const email = req.params?.email?.toLowerCase();
  
        console.log(`➡️ GET /api/profiles: `);
  
        // Fetch the profile from the ServiceNow API.
        const profile = await ProfilesApiService.getProfile(email);
        res.jsonBody.results = profile ?? [];
        console.log(`   ✅ GET /api/profiles: response status ${res.status}; ${profile.length} profiles returned`);
        return res;
  
    }
    catch (error) {
      console.error(`   ❌ GET /api/profiles: ${error}`);
      res.status = 500;
      res.jsonBody = { error: error.message };
      return res;
    }
}

app.http("profiles", {
    methods: ["GET"],
    authLevel: "anonymous",
    route: "profiles/{*email}",
    handler: profiles,
  });