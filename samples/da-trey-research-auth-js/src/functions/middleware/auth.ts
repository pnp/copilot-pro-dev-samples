import { HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import { EntraJwtPayload, getEntraJwksUri, TokenValidator } from "jwt-validate";
import ConsultantApiService from "../../services/ConsultantApiService";
import { ApiConsultant } from "../../model/apiModel";
import config from "../../config";

export interface UserInfo {
    id?: string;
    name: string;
    email: string;
}

function getToken(req: HttpRequest): string | undefined {
    return req.headers.get("authorization")?.split(" ")[1];
}

async function validateToken(token: string): Promise<EntraJwtPayload | null> {
    // gets the JWKS URL for the Microsoft Entra common tenant
    const entraJwksUri = await getEntraJwksUri();

    // create a new token validator with the JWKS URL
    const validator = new TokenValidator({
        jwksUri: entraJwksUri
    });

    try {
        // validate the token
        return await validator.validateToken(token, {
            allowedTenants: [config.entraAppTenantId],
            audience: config.entraAppClientId,
            scp: ["access_as_user"],
            ver: "2.0",
        });
    }
    catch (ex) {
        return null;
    }
}

function extractUserInfoFromToken(token: EntraJwtPayload): UserInfo {
    const { name, preferred_username } = token
    return { name, email: preferred_username };
}

async function ensureConsultant(userInfo: UserInfo): Promise<ApiConsultant | null> {
    let consultant: ApiConsultant | null = null;
    consultant = await ConsultantApiService.getApiConsultantByEmail(userInfo.email);
    // if no consultant found, create a default one based on logged in user info for this demo
    if (!consultant) {
        consultant = await ConsultantApiService.createApiConsultant({
            name: userInfo.name,
            email: userInfo.email,
            phone: "1-555-456-7890",
            consultantPhotoUrl: "https://bobgerman.github.io/fictitiousAiGenerated/Unknown.jpg",
            location: {
                street: "5 Wayside Rd.",
                city: "Burlington",
                state: "MA",
                country: "USA",
                postalCode: "01803",
                latitude: 42.5048,
                longitude: -71.1956
            },
            skills: ["C#", "JavaScript", "TypeScript", "React", "Node.js"],
            certifications: ["MCSADA", "Azure Developer Associate", "MCAAF", "Azure AI Fundamentals"],
            roles: ["Project lead", "Developer", "Architect", "DevOps"],
        });
    }
    return consultant;
}

function successResponse(response: ResponseInit): HttpResponseInit {
    return withHeaders(response)
}

function errorResponse(status: number, error: string, message: string): HttpResponseInit {
    return withHeaders({
        status,
        jsonBody: {
            error,
            message
        }
    })
}

function withHeaders(res: HttpResponseInit): HttpResponseInit {
    const headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    return {
        ...res,
        headers
    }
}

export function withAuth(
    handler: (req: HttpRequest, context: InvocationContext, userInfo?: UserInfo) => Promise<HttpResponseInit>
) {
    return async (req: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
        const token = getToken(req);
        if (!token) {
            context.log("No token provided in request headers");
            return errorResponse(401, "Unauthorized", "Authentication token is required");
        }

        const validToken = await validateToken(token);
        if (!validToken) {
            context.log("Invalid or expired token");
            return errorResponse(401, "Unauthorized", "Invalid or expired authentication token");
        }

        const userInfo = extractUserInfoFromToken(validToken);
        const consultant = await ensureConsultant(userInfo);

        // update userInfo with consultant ID for more efficient lookups
        userInfo.id = consultant?.id || userInfo.id;

        try {
            const response = await handler(req, context, userInfo);
            return successResponse(response);
        }
        catch (error) {
            context.error("Handler execution error:", error);
            return errorResponse(500, "Internal Server Error", "An error occurred while processing the request");
        }
    };
}
