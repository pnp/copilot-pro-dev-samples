/* This code sample provides a starter kit to implement server side logic for your Teams App in TypeScript,
 * refer to https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference for complete Azure Functions
 * developer guide.
 */

import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

// ADDED FOR TOKEN VALIDATION
import { TokenValidator, ValidateTokenOptions, getEntraJwksUri } from 'jwt-validate';
let validator: TokenValidator;
// END ADDED FOR TOKEN VALIDATION

import repairRecords from "../repairsData.json";

/**
 * This function handles the HTTP request and returns the repair information.
 *
 * @param {HttpRequest} req - The HTTP request.
 * @param {InvocationContext} context - The Azure Functions context object.
 * @returns {Promise<Response>} - A promise that resolves with the HTTP response containing the repair information.
 */
export async function repairs(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  context.log("HTTP trigger function processed a request.");


  const isLocal = !process.env.WEBSITE_INSTANCE_ID;

  if (isLocal) {
    context.log("Running locally");
      // Only validate the token if the function is running locally, otherwise the token will be validated by Easy Auth in Azure
      // ADDED FOR TOKEN VALIDATION
      // Try to validate the token and get user's basic information
      try {
        const { AAD_APP_CLIENT_ID, AAD_APP_TENANT_ID, AAD_APP_OAUTH_AUTHORITY } = process.env;
        const token = req.headers.get("Authorization")?.split(" ")[1];
        if (token) {

          if (!validator) {
            const entraJwksUri = await getEntraJwksUri(AAD_APP_TENANT_ID);
            validator = new TokenValidator({
              jwksUri: entraJwksUri
            });
            console.log("Token validator created");
          }

          const options: ValidateTokenOptions = {
            audience: `${AAD_APP_CLIENT_ID}`,
            // NOTE: Issuer will be different for non-public clouds
            issuer: `${AAD_APP_OAUTH_AUTHORITY}/v2.0`,
            scp: ["repairs_read"]
          };

          const validToken = await validator.validateToken(token, options);

          const userId = validToken.oid;
          const userName = validToken.name;
          console.log(`Token is valid for user ${userName} (${userId})`);
        } else {
          console.error("No token found in request");
          throw (new Error("No token found in request"));
        }
      }
      catch (ex) {
        // Token is missing or invalid - return a 401 error
        console.error(ex);
        return  {
          status: 401
        };
      }
      // END ADDED FOR TOKEN VALIDATION
  } else {
    context.log("Running in Azure");
    // No need to validate token in Azure, as the function is secured by Easy Auth
  }

  // Initialize response.
  const res: HttpResponseInit = {
    status: 200,
    jsonBody: {
      results: repairRecords,
    },
  };

  // Get the assignedTo query parameter.
  const assignedTo = req.query.get("assignedTo");



  // If the assignedTo query parameter is not provided, return the response.
  if (!assignedTo) {
    return res;
  }

  // Filter the repair information by the assignedTo query parameter.
  const repairs = repairRecords.filter((item) => {
    const fullName = item.assignedTo.toLowerCase();
    const query = assignedTo.trim().toLowerCase();
    const [firstName, lastName] = fullName.split(" ");
    return fullName === query || firstName === query || lastName === query;
  });

  // Return filtered repair records, or an empty array if no records were found.
  res.jsonBody.results = repairs ?? [];
  return res;
}

app.http("repairs", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: repairs,
});
