from azure.identity import DefaultAzureCredential
import os
import asyncio
import logging
import datetime
import logging
import boto3

from dotenv import load_dotenv
load_dotenv()

# Configuration potential
VALID_CREDENTIAL_LIFETIME = datetime.timedelta(days=2)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)


from msgraph import GraphServiceClient
from msgraph.generated.service_principals.service_principals_request_builder import ServicePrincipalsRequestBuilder
from msgraph.generated.service_principals.item.owned_objects.graph_application.graph_application_request_builder import GraphApplicationRequestBuilder
from msgraph.generated.applications.item.remove_key.remove_key_post_request_body import RemoveKeyPostRequestBody
from msgraph.generated.applications.item.add_password.add_password_post_request_body import AddPasswordPostRequestBody
from msgraph.generated.models.password_credential import PasswordCredential

async def get_service_principal_from_application(client, client_id):
    query_params = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
        filter=f"appId eq '{client_id}'",
        select=["id"]
    )
    request_config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
        query_parameters=query_params,
    )
    request_config.headers.add("ConsistencyLevel", "eventual")

    value = await client.service_principals.get(request_configuration=request_config)
    sp_id = value.value[0].id
    return sp_id

async def get_applications_owned_by_service_principal(client, service_principal_id):
    query_params = GraphApplicationRequestBuilder.GraphApplicationRequestBuilderGetQueryParameters(
        select=["id", "passwordCredentials"]
    )

    request_config = GraphApplicationRequestBuilder.GraphApplicationRequestBuilderGetRequestConfiguration(
        query_parameters=query_params
    )
    request_config.headers.add("ConsistencyLevel", "eventual")
    applications = await client.service_principals.by_service_principal_id(service_principal_id).owned_objects.graph_application.get(request_configuration=request_config)
    return applications.value

def is_cred_too_old(cred):
    return cred.end_date < datetime.now()

async def purge_oldest_credentials(client, object_id, creds):
    # Delete by order of expiration, starting with the closest to expiration
    creds.sort(key=lambda cred: cred.end_date_time)
    while len(creds) > 1:
        oldest_cred = creds.pop(0)
        logging.info(f"Deleting credential {oldest_cred.key_id}: {oldest_cred.display_name} for {object_id}")
        request_body = RemoveKeyPostRequestBody()
        request_body.key_id = oldest_cred.key_id
        await client.applications.by_application_id(object_id).remove_password.post(request_body)

async def tidy_application_credentials(client, application):
    id = application.id
    creds = application.password_credentials
    if creds:
        await purge_oldest_credentials(client, id, creds)

async def create_new_application_credential(client, application):
    id = application.id
    logging.info(f"Creating new credential for {id}")
    end_date_time = datetime.datetime.now() + VALID_CREDENTIAL_LIFETIME
    request_body = AddPasswordPostRequestBody(
        password_credential=PasswordCredential(
            end_date_time=end_date_time,
            display_name=f"generated credential, expires at {end_date_time}"
        )
    )
    creds = await client.applications.by_application_id(id).add_password.post(request_body)

    return creds

def store_new_credential(smclient, application, creds):
    secret_id = f"{application.id}"
    try:
        smclient.put_secret_value(
            SecretId=secret_id,
            SecretString=creds.secret_text
        )
    except smclient.exceptions.ResourceNotFoundException as e:
        logging.warn(f"creating secret as secret did not exist for {application.id}: {e}")
        smclient.create_secret(
            Name=secret_id,
        )
        store_new_credential(smclient, application, creds)
    except Exception as e:
        logging.error(f"Failed to store secret for {application.id}: {e}")
        return False
    return True

async def main(gclient, smclient, client_id) -> int:
    my_service_principal_id = await get_service_principal_from_application(gclient, client_id)
    applications = await get_applications_owned_by_service_principal(gclient, my_service_principal_id)
    any_failed = False
    for application in applications:
        await tidy_application_credentials(gclient, application)
        creds = await create_new_application_credential(gclient, application)
        result = store_new_credential(smclient, application, creds)
        if not result:
            any_failed = True
    
    return 1 if any_failed else 0

if __name__ == "__main__":
    gclient = GraphServiceClient(credentials=DefaultAzureCredential(), scopes=["https://graph.microsoft.com/.default"])
    smclient = boto3.client("secretsmanager")
    result = asyncio.run(main(gclient, smclient, os.getenv("AZURE_CLIENT_ID")))
    os._exit(result)