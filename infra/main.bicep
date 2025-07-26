// ==== パラメータ ====
param location string
param pgServerName string
param pgDbName string
param pgAdminUser string
@secure()
param pgAdminPassword string
param cosmosAccountName string
param cosmosDbName string
param cosmosContainerName string
param cosmosPartitionKey string
param cosmosDbThroughput int
param aiFoundryName string
param aiProjectName string
param aiModelDeploymentName string = 'gpt-4o'

// ===== PostgreSQL Flexible Server =====
resource pgServer 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: pgServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: pgAdminUser
    administratorLoginPassword: pgAdminPassword
    storage: { storageSizeGB: 32 }
    highAvailability: { mode: 'Disabled' }
    network: { publicNetworkAccess: 'Enabled' }
  }
}

// ===== PostgreSQL DB作成 =====
resource pgDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: pgServer
  name: pgDbName
  properties: {}
}

// ===== FWルール =====
resource pgFirewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: pgServer
  name: 'allowall'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

// ===== Cosmos DB アカウント =====
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: []
    publicNetworkAccess: 'Enabled'
  }
}

// ===== Cosmos DB データベース =====
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' = {
  parent: cosmosAccount
  name: cosmosDbName
  properties: {
    resource: {
      id: cosmosDbName
    }
  }
}

// ===== Cosmos DB コンテナ =====
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = {
  parent: cosmosDb
  name: cosmosContainerName
  properties: {
    resource: {
      id: cosmosContainerName
      partitionKey: {
        paths: [cosmosPartitionKey]
        kind: 'Hash'
      }
    }
    options: {
      throughput: cosmosDbThroughput
    }
  }
}

// ==== AI Foundry Account ====
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    customSubDomainName: toLower(aiFoundryName)
    disableLocalAuth: false // ローカル認証を無効化（本番環境では非推奨）※ https://learn.microsoft.com/en-us/azure/ai-services/disable-local-auth
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
  }
}

// ==== AI Foundry Project ====
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

// ==== AI Foundry Model Deployment ====
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: aiModelDeploymentName
  sku : {
    capacity: 35
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: aiModelDeploymentName
      format: 'OpenAI'
    }
  }
}

// ===== 出力 =====
output pgServerFqdn string = pgServer.properties.fullyQualifiedDomainName
output cosmosAccountEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosAccountName string = cosmosAccountName
output cosmosDbName string = cosmosDbName
output cosmosContainerName string = cosmosContainerName
output aiFoundryName string = aiFoundry.name
output aiProjectName string = aiProject.name
output aiModelDeploymentName string = modelDeployment.name
