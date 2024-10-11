
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { HttpError } from "../services/utilities";
import IncidentsApiService from "../services/snow_incidents";

/**
 * This function handles the HTTP request and returns the incidents information.
 *
 * @param {HttpRequest} req - The HTTP request.
 * @param {InvocationContext} context - The Azure Functions context object.
 * @returns {Promise<Response>} - A promise that resolves with the HTTP response containing the incident information.
 */
export async function incidents(
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
      const id = req.params?.id; // Incident ID
      // Need to implement authentication to get the address from context, for now lets use Fred Luddy as the current user
      const email = 'fred.luddy@example.com'
      let body = null;

      switch (req.method) {
        case "GET": {

          if (id) {
            // Fetch the incident from the ServiceNow API.
            console.log(`➡️ GET /api/incidents/${id}: `);
            const incident = await IncidentsApiService.getIncident(id);
            res.jsonBody.results = incident ?? [];
            console.log(`   ✅ GET /api/incidents${id}: response status ${res.status}; ${incident.length} incidents returned`);
            return res;
          }

          // Fetch all incidents from the ServiceNow API.
          console.log(`➡️ GET /api/incidents: `);
          const incidents = await IncidentsApiService.getIncidents();
          res.jsonBody.results = incidents ?? [];
          console.log(`   ✅ GET /api/incidents: response status ${res.status}; ${incidents.length} incidents returned`);
          return res;

        }
        case "POST": {
          try {
            const bd = await req.text();
            body = JSON.parse(bd);
          } catch (error) {
            throw new HttpError(400, `No body to process this request.`);
          }
          if (body) {
            // Create a new incident in ServiceNow.
            console.log(`➡️ POST /api/incidents: `);
            const incident = await IncidentsApiService.createIncident(email, body["short_description"], body["description"]);
            res.jsonBody.results = incident ?? [];
            console.log(`   ✅ POST /api/incidents: response status ${res.status}; ${incident.number} incident created!`);
            return res;
          }
        }
        default: {
            throw new Error(`Method not allowed: ${req.method}`);
        }
      }

  }
  catch (error) {
    console.error(`   ❌ GET /api/incidents: ${error}`);
    res.status = 500;
    res.jsonBody = { error: error.message };
    return res;
  }

}

app.http("incidents", {
  methods: ["GET", "POST"],
  authLevel: "anonymous",
  route: "incidents/{*id}",
  handler: incidents,
});
