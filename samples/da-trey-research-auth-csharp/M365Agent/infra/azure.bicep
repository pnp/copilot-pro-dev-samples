@maxLength(20)
@minLength(4)
param resourceBaseName string
param functionAppSKU string
param entraAppClientId string
param entraAppTenantId string

param location string = resourceGroup().location
param serverfarmsName string = resourceBaseName
param functionAppName string = resourceBaseName
param storageAccountName string = resourceBaseName

// Storage account for Azure Table Storage
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

var storageAccountConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'

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
          value: 'dotnet-isolated'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'SCM_ZIPDEPLOY_DONOT_PRESERVE_FILETIME'
          value: '1'
        }
        {
          name: 'STORAGE_ACCOUNT_CONNECTION_STRING'
          value: storageAccountConnectionString
        }
        {
          name: 'ENTRA_APP_CLIENT_ID'
          value: entraAppClientId
        }
        {
          name: 'ENTRA_APP_TENANT_ID'
          value: entraAppTenantId
        }
      ]
      ftpsState: 'FtpsOnly'
    }
  }
}

var apiEndpoint = 'https://${functionApp.properties.defaultHostName}'

// The output will be persisted in .env.{envName}.
output API_FUNCTION_ENDPOINT string = apiEndpoint
output API_FUNCTION_RESOURCE_ID string = functionApp.id
output OPENAPI_SERVER_URL string = apiEndpoint
output SECRET_STORAGE_ACCOUNT_CONNECTION_STRING string = storageAccountConnectionString
