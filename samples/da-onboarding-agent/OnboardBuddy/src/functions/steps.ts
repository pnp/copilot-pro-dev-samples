import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

import { Step, CompletedStep } from "../model/Step";
import { HttpError, ErrorResult  } from "../model/ErrorHandling";
import { authMiddleware } from "./middleware/authMiddleware";

/**
 * This function handles the HTTP request and returns the project information.
 *
 * @param {HttpRequest} req - The HTTP request.
 * @param {InvocationContext} context - The Azure Functions context object.
 * @returns {Promise<Response>} - A promise that resolves with the HTTP response containing the project information.
 */

// Define a Response interface.
interface Response extends HttpResponseInit {
    status: number;
    jsonBody: {
        results: Step[] | Step | ErrorResult;
    };
}
export async function steps(
    req: HttpRequest,
    context: InvocationContext
): Promise<Response> {

    context.log("HTTP trigger function steps processed a request.");

    // Initialize response.
    const res: Response = {
        status: 200,
        jsonBody: {
            results: [],
        },
    };

    try {

        // Check if the request is authorized using boilerplate token validation
        const validatedClaims = await authMiddleware(req);
        if (!validatedClaims || !validatedClaims.name || !validatedClaims.oid) {
            throw new HttpError(401, `Unauthorized`);
        }

        const path = req.params?.id?.toLowerCase();
        let body = null;
        switch (req.method) {
            case "GET": {
                if (!path) {
                    console.log(`➡️ GET /steps for ${validatedClaims.name} (${validatedClaims.oid})`);
                    console.log(`   ✅ GET /steps: response status ${res.status}; 0 projects returned`);
                    // return all steps
                } else if (path?.toLocaleLowerCase() === "next") {
                    console.log(`➡️ GET /steps/next for ${validatedClaims.name} (${validatedClaims.oid})`);
                    console.log(`   ✅ GET /steps/next: response status ${res.status}; 0 projects returned`);
                    // return next step
                } else {
                    throw new HttpError(404, `No such path: ${path}`);
                }
            }
            case "POST": {
                if (path?.toLocaleLowerCase() !== "completed") {
                    throw new HttpError(400, `No such path: ${path}`);
                }
                // Check to be sure the step ID provided is the current step for this user, else throw an error

                // Mark step as completed

                try {
                    const bd = await req.text();
                    body = JSON.parse(bd);
                } catch (error) {
                    throw new HttpError(400, `No body to process this request.`);
                }
                if (body) {
                    const stepId = body["stepId"];
                    if (!stepId) {
                        // Get the step by ID from the data store
                        const selectedStep = {} as Step; // getStepById(stepId);
                        // Make sure the step ID is the current step
                        if (!selectedStep.isCurrent) {
                            throw new HttpError(400, `Step ${stepId} is not the current step`);
                        }
                        // Mark the step as completed    
                        console.log(`➡️ POST /steps/completed for ${validatedClaims.name} (${validatedClaims.oid})`);
                        console.log(`   ✅ POST /steps/completed: response status ${res.status}; 1 step updated`);
                    }
               }
            }
            default: {
                throw new HttpError(400, `Method not allowed: ${req.method}`);
            }
        }

    } catch (error) {

        const status = <number>error.status || <number>error.response?.status || 500;
        console.log(`   ⛔ Returning error status code ${status}: ${error.message}`);

        res.status = status;
        res.jsonBody.results = {
            status: status,
            message: error.message
        };
        return res;
    }
}

app.http("steps", {
    methods: ["GET", "POST"],
    authLevel: "anonymous",
    route: "steps/{*path}",
    handler: steps
});




// app.http("next", {
//   methods: ["GET", "POST"],
//   route: "step/{*path}",
//   authLevel: "anonymous",   // Disable function auth; auth is handled in the code below
//   handler: async (req: HttpRequest, context: InvocationContext) => {
//     // Check if the request is authorized
//     const validatedClaims = await authMiddleware(req);
//     if (!validatedClaims || !validatedClaims.name || !validatedClaims.oid) {
//       return {
//         status: 401,
//         body: "Unauthorized",
//       };
//     }
//     console.log (`Validated token for ${validatedClaims.name} (${validatedClaims.oid})`);
    
//     // Call the actual handler function
//     switch (req.method) {
//       case "GET":
//         return await getNextStep(req, context, validatedClaims.oid, validatedClaims.name);
//       case "POST":
//         return await completedStep(req, context, validatedClaims.oid, validatedClaims.name);
//       default:
//         return {
//           status: 405,
//           body: "Method Not Allowed",
//         };
//     }
//   },
// });

// export async function getNextStep(
//   req: HttpRequest,
//   context: InvocationContext,
//   userId: string,
//   userName: string
// ): Promise<HttpResponseInit> {
  
//   // Initialize response.
//   const res: HttpResponseInit = {
//     status: 200,
//     jsonBody: {
//       results: {},
//     },
//   };

//   return res;
// }

//#region Cutting room floor

// /**
//  * This function handles the HTTP request and returns the repair information.
//  *
//  * @param {HttpRequest} req - The HTTP request.
//  * @param {InvocationContext} context - The Azure Functions context object.
//  * @returns {Promise<Response>} - A promise that resolves with the HTTP response containing the repair information.
//  */
// export async function repairs(
//   req: HttpRequest,
//   context: InvocationContext,
//   userId: string,
//   userName: string
// ): Promise<HttpResponseInit> {
//   context.log("HTTP trigger function processed a request.");

//   // Initialize response.
//   const res: HttpResponseInit = {
//     status: 200,
//     jsonBody: {
//       results: repairRecords,
//     },
//   };

//   // Get the assignedTo query parameter.
//   const assignedTo = req.query.get("assignedTo");

//   // If the assignedTo query parameter is not provided, return the response.
//   if (!assignedTo) {
//     return res;
//   }

//   // Filter the repair information by the assignedTo query parameter.
//   const repairs = repairRecords.filter((item) => {
//     const fullName = item.assignedTo.toLowerCase();
//     const query = assignedTo.trim().toLowerCase();
//     const [firstName, lastName] = fullName.split(" ");
//     return fullName === query || firstName === query || lastName === query;
//   });

//   // Return filtered repair records, or an empty array if no records were found.
//   res.jsonBody.results = repairs ?? [];
//   return res;
// }

//#endregion