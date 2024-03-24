# ResAI Python Azure Functions

## Install Deps:
- `pip install -r requirements.txt`

## Deploy to Serverless (without container)
`func azure functionapp publish <function-app-name>`

## Azure CLI  Helpers
- `az login`
- `az acr login --name <name>`
- `az account set --subscription <subscription-id>`
- `az account list --output table`

## Docker Helpers

- `docker build --tag <repo-name>.azurecr.io/mytestapp .`
- `docker push <repo-name>.azurecr.io/mytestapp`
- `docker run -p 8080:80 -it <repo-name>.azurecr.io/mytestapp`
- `docker exec -it 2689f49ba6f6 /bin/bash`
- `az functionapp config container set --image <repo-name>.azurecr.io/mytestapp --registry-password <SECURE_PASSWORD>--registry-username <USER_NAME> --name <APP_NAME> --resource-group <RESOURCE_GROUP>`

## Configure Azure Function with Authentication
1. Go to Azure Portal -> Settings -> Authentication.
2. Click the "Add Provider" button. 
3. Select Microsoft.
4. Fill in all the fields. Here's some notable fields:
   1. Supported account types: Current tenant - Single tenant
   2. Client secret value:  blank
   3. Issuer URL:  blank
   4. Allow token audiences: blank
   5. Client application requirement:  Allow request from any application.
   6. Identity requirement: Allow request from any identity.
   7. Tenant requirement:  Allow request from specific tenants.
   8. Allow tenants:  Your tenant ID
5. Click add (No need to do anything with permissions).

## Configure Entra App registration for this Azure Function
1. Go to Azure Portal -> Microsoft Entra ID -> App registrations.
2. Create your app.  Give it whatever name you want.
3. From within your newly created Entra app, go to Authentication on left side nav.
4. Add Platform
5. Single-page application
6. Add URI.  Add both localhost and web app domain. 
7. Check these boxes:
   1. Access tokens (used for implicit flows).
   2. ID tokens (used for implicit and hybrid flows).
   3. Supported account types: Accounts in this organization directly only. 
   4. Advanced Settings: Allow public client flows. 
8. App Roles - Create two app roles: One called `Api.ReadWrite.All` and `Api.Read.All`.  Note:  Not sure if these are needed, but hey we're created.
9. Go to Expose an API - Enable the "Application ID URI".  Value will look like this `api://<scope-id>`.
10. Add two scopes.  Will look like this:  `api://<scope-id>/Api.ReadWrite`.  Note: Not sure if these are currently needed.
11. API Permissions - Add your Azure Function App with the two new scopes.