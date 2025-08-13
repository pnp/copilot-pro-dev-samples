using M365.Comms.API.Auth;
using M365.Comms.API.Models;
using M365.Comms.API.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.Identity.Web;
using Microsoft.OpenApi.Any;
using Microsoft.OpenApi.Models;
using PnP.Core.Services;
using System.Text.Json.Serialization;

namespace M365.Comms.API
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            // Add Authenticatio services to the container.
            builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
                .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"))
                .EnableTokenAcquisitionToCallDownstreamApi()
                .AddDistributedTokenCaches();


            if (builder.Environment.IsDevelopment())
            {
                builder.Services.AddDistributedMemoryCache();
            }
            else
            {
                builder.Services.AddDistributedSqlServerCache(options =>
                {
                    options.ConnectionString = builder.Configuration.GetValue<string>("AZURE_SQL_CONNECTIONSTRING");
                    options.SchemaName = "dbo";
                    options.TableName = "TokenCache";
                });
            }

            // Register IHttpContextAccessor
            builder.Services.AddHttpContextAccessor();

            // Adjust the enums to be serialized as strings
            builder.Services.AddControllers().AddJsonOptions(options =>
            {
                options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
            });

            // For Mocking the Message Service
            var UseMocking = builder.Configuration.GetValue<bool?>("UseMockService");

            if (UseMocking != null && UseMocking == true)
            {
                builder.Services.AddScoped<IMessageService, MockMessageService>();
            }
            else
            {

                // Use PnP Core SDK services to process messages
                builder.Services.AddScoped<IMessageService, PnPSharePointMessageService>();
                builder.Services
                    .AddScoped<IAuthenticationProvider, WebAPICustomPnPProvider>(sp =>
                    {
                        var tokenAcquisition = sp.GetRequiredService<ITokenAcquisition>();
                        var logger = sp.GetRequiredService<ILogger<WebAPICustomPnPProvider>>();
                        return new WebAPICustomPnPProvider(tokenAcquisition, logger);
                    })
                    .AddSingleton<IConfiguration>(builder.Configuration)
                    .AddScoped<IM365PnPContextFactory, M365PnPContextFactory>();

                // Add the PnP Core SDK library services
                builder.Services.AddPnPCore(options =>
                {
                    options.PnPContext.GraphFirst = true;
                });
            }
                        

            // Set up OpenAPI to generate OpenAPI specification
            // Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
            AddOpenApiAndConfigure(builder);

            builder.Services.AddLogging(loggingBuilder =>
            {
                loggingBuilder.AddConsole();
                loggingBuilder.AddDebug();

            });

            // Add Logging to the application when not building in development mode
            builder.Logging.AddApplicationInsights(
                    configureTelemetryConfiguration: (config) =>
                        config.ConnectionString = builder.Configuration["ApplicationInsights:ConnectionString"],
                        configureApplicationInsightsLoggerOptions: (options) => { }
                );

            var app = builder.Build();

            // Configure the exception handling features.
            app.UseExceptionHandler(builder =>
            {
                builder.Run(async context =>
                {
                    var exception = context.Features.Get<IExceptionHandlerFeature>()?.Error;

                    if (exception is UnauthorizedAccessException)
                    {
                        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                        await context.Response.WriteAsync("Unauthorized: Token has expired or re-authentication required.");
                    }
                    else
                    {
                        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
                        await context.Response.WriteAsync("An unexpected error occurred.");
                    }
                });
            });

            // Configure the HTTP request pipeline.
            if (app.Environment.IsDevelopment())
            {
                app.MapOpenApi();
                // Use https://localhost:7200/openapi/v1.json to get the resulting OpenAPI specification
            }

            app.UseHttpsRedirection();

            app.UseAuthentication();

            app.UseAuthorization();

            app.MapControllers();

            app.Run();
        }

        /// <summary>
        /// Adds OpenAPI and configures it.
        /// </summary>
        /// <param name="builder"></param>
        /// <exception cref="ApplicationException"></exception>
        private static void AddOpenApiAndConfigure(WebApplicationBuilder builder)
        {
            //Used from sample fragment to configure the OpenAPI Specification
            // https://github.com/microsoftgraph/msgraph-sample-copilot-plugin
            builder.Services.AddOpenApi((options) =>
            {
                // Add document transform to add additional info
                options.AddDocumentTransformer((document, context, cancellationToken) =>
                {
                    var settings = builder.Configuration
                        .Get<AppSettings>() ?? throw new ApplicationException("Could not load settings from appsettings.json");

                    // Add the dev tunnel URL if specified in app settings
                    if (!string.IsNullOrEmpty(settings.ServerUrl))
                    {
                        // Clear localhost entries added automatically
                        document.Servers.Clear();
                        document.Servers.Add(new()
                        {
                            Url = settings.ServerUrl,
                        });
                    }


                    _ = settings.AzureAd?.Instance ?? throw new ApplicationException(nameof(settings.AzureAd.Instance));
                    _ = settings.AzureAd?.TenantId ?? throw new ApplicationException(nameof(settings.AzureAd.TenantId));
                    _ = settings.AzureAd?.ClientId ?? throw new ApplicationException(nameof(settings.AzureAd.ClientId));

                    var baseAuthUrl = settings.AzureAd.Instance + settings.AzureAd.TenantId;
                    var apiScope = $"api://{settings.AzureAd.ClientId}/.default";

                    // Add the OAuth2 security scheme
                    document.Components ??= new OpenApiComponents();
                    document.Components.SecuritySchemes.Add("OAuth2", new()
                    {
                        Type = SecuritySchemeType.OAuth2,
                        Flows = new()
                        {
                            AuthorizationCode = new()
                            {
                                AuthorizationUrl = new Uri($"{baseAuthUrl}/oauth2/v2.0/authorize"),
                                TokenUrl = new Uri($"{baseAuthUrl}/oauth2/v2.0/token"),
                                RefreshUrl = new Uri($"{baseAuthUrl}/oauth2/v2.0/token"),
                                Scopes = new Dictionary<string, string>()
                    {
                        { apiScope, "Access the API on your behalf" },
                    },
                            },
                        },
                    });

                    // Add security requirement to all endpoints
                    document.SecurityRequirements.Add(new()
                    {
                        {
                            new OpenApiSecurityScheme
                            {
                                Reference = new()
                                {
                                    Type = ReferenceType.SecurityScheme,
                                    Id = "OAuth2",
                                },
                            },
                            [
                                apiScope
                            ]
                        },
                    });

                    return Task.CompletedTask;
                });

                // Add operation transform to add x-openai-isConsequential to override prompt behavior
                // See https://learn.microsoft.com/microsoft-365-copilot/extensibility/api-plugin-confirmation-prompts
                options.AddOperationTransformer((operation, context, cancellationToken) =>
                {
                    if (string.Compare(operation.OperationId, "SendTransactionReport", StringComparison.Ordinal) == 0)
                    {
                        operation.Extensions.Add("x-openai-isConsequential", new OpenApiBoolean(false));
                    }

                    // Update responses to include individual properties inline
                    var messageSchema = new OpenApiSchema
                    {
                        Type = "object",
                        Properties = new Dictionary<string, OpenApiSchema>
                        {
                            { "Id", new OpenApiSchema { Type = "integer", Format = "int32" } },
                            { "MarkdownContent", new OpenApiSchema { Type = "string" } },
                            { "Approval", new OpenApiSchema { Type = "string", Enum = new List<IOpenApiAny> { new OpenApiString("Pending"), new OpenApiString("Approved"), new OpenApiString("Rejected"), new OpenApiString("Cancelled"), new OpenApiString("Submitted") } } },
                            { "SendToSharePoint", new OpenApiSchema { Type = "boolean" } },
                            { "SendToTeams", new OpenApiSchema { Type = "boolean" } },
                            { "SendToOutlook", new OpenApiSchema { Type = "boolean" } },
                            { "ReviewItemUrl", new OpenApiSchema { Type = "string" } }
                        }
                    };

                    if (operation.Responses.ContainsKey("200"))
                    {
                        if (operation.Responses["200"].Content.ContainsKey("text/plain"))
                        {
                            operation.Responses["200"].Content["text/plain"].Schema = messageSchema;
                        }
                        if (operation.Responses["200"].Content.ContainsKey("application/json"))
                        {
                            operation.Responses["200"].Content["application/json"].Schema = messageSchema;
                        }
                        if (operation.Responses["200"].Content.ContainsKey("text/json"))
                        {
                            operation.Responses["200"].Content["text/json"].Schema = messageSchema;
                        }
                    }

                    return Task.CompletedTask;
                });
            });
        }
    }
}
