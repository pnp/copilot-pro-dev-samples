@maxLength(20)
@minLength(4)
param resourceBaseName string
param functionAppSKU string
param aadAppClientId string
@secure()
param aadAppClientSecret string
param aadAppTenantId string
param aadAppOauthAuthorityHost string
param location string = resourceGroup().location
param serverfarmsName string = resourceBaseName
param functionAppName string = resourceBaseName


// Compute resources for Azure Functions
resource serverfarms 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: serverfarmsName
  location: location
  sku: {
    name: functionAppSKU
  }
  properties: {}
}

// Azure Functions that hosts your function code
resource functionApp 'Microsoft.Web/sites@2021-02-01' = {
  name: functionAppName
  kind: 'functionapp'
  location: location
  properties: {
    serverFarmId: serverfarms.id
    httpsOnly: true
    siteConfig: {
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'AAD_APP_CLIENT_ID'
          value: aadAppClientId
        }
        {
          name: 'AAD_APP_CLIENT_SECRET'
          value: aadAppClientSecret
        }
        {
          name: 'AAD_APP_TENANT_ID'
          value: aadAppTenantId
        }
        {
          name: 'AAD_APP_OAUTH_AUTHORITY_HOST'
          value: aadAppOauthAuthorityHost
        }
      ]
      ftpsState: 'FtpsOnly'
    }
  }
}
var apiEndpoint = 'https://${functionApp.properties.defaultHostName}'
var oauthAuthority = uri(aadAppOauthAuthorityHost, aadAppTenantId)
var aadApplicationIdUri = 'api://${aadAppClientId}'

// Configure Azure Functions to use Azure AD for authentication.
resource authSettings 'Microsoft.Web/sites/config@2021-02-01' = {
  parent: functionApp
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: oauthAuthority
          clientId: aadAppClientId
        }
        validation: {
          allowedAudiences: [
            aadAppClientId
            aadApplicationIdUri
          ]
        }
      }
    }
  }
}

// The output will be persisted in .env.{envName}.
output API_FUNCTION_ENDPOINT string = apiEndpoint
output API_FUNCTION_RESOURCE_ID string = functionApp.id
output OPENAPI_SERVER_URL string = apiEndpoint
