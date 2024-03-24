import logging
import os
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse

from azure.functions import HttpRequest, HttpResponse
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

SEARCH_SERVICE_NAME = os.getenv("SEARCH_SERVICE_NAME")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
AZURE_STORAGE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')


def main(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    req_body = req.get_json()
    search_text = req_body.get('search_text')
    content = req_body.get('content')
    top = req_body.get('top')
    file = req_body.get('file')

    image_embedding = None
    content_embedding = None

    response = search_data(
        search_service_name=SEARCH_SERVICE_NAME,
        index_name=SEARCH_INDEX_NAME,
        image_embedding=image_embedding,
        search_text=search_text,
        content_embedding=content_embedding,
        content=content,
        top=top
    )

    response = update_response_with_sas_token(response)

    data = {
        'success': True,
        'data': response
    }

    return HttpResponse(body=json.dumps(data), mimetype="application/json")


def search_data(
        search_service_name: str,
        index_name: str,
        search_text: str = "",
        image_embedding=[],
        content="",
        content_embedding=[],
        top: int = 20
):
    url = f"https://{search_service_name}.search.windows.net/indexes/{index_name}/docs/search?api-version=2023-11-01"

    print(f"Posting search to {url}")

    headers = {
        'Content-type': 'application/json',
        'api-key': SEARCH_API_KEY
    }

    data = {
        "count": True,
        "select": "title, file_path, tags, content",
        "top": top,
    }

    if (image_embedding or content_embedding):
        data["vectorQueries"] = []

    if (image_embedding):
        data["vectorQueries"].append(
            {
                "vector": image_embedding,
                "k": top,
                "fields": "image_vector",
                "kind": "vector",
                "exhaustive": True
            }
        )

    if (content_embedding):
        data["vectorQueries"].append(
            {
                "vector": content_embedding,
                "k": top,
                "fields": "content_vector",
                "kind": "vector",
                "exhaustive": True
            }
        )

    if (search_text):
        data["search"] = search_text

    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Search complete with status_code {response.status_code}")
    return response.json()


def update_response_with_sas_token(response):
    for item in response['value']:
        file_path = item['file_path']
        sas_token = get_blob_sas_token(file_path)
        final_path = f"{file_path}?{sas_token}"
        item['file_path'] = final_path
    return response


def get_blob_sas_token(blob_url: str):
    blob_full_name = get_blob_full_name(blob_url)
    sas_token = generate_blob_sas(account_name=AZURE_STORAGE_ACCOUNT_NAME,
                                  container_name=AZURE_STORAGE_CONTAINER_NAME,
                                  blob_name=blob_full_name,
                                  account_key=AZURE_STORAGE_ACCOUNT_KEY,
                                  permission=BlobSasPermissions(read=True),
                                  expiry=datetime.utcnow() + timedelta(hours=1))  # Token valid for 1 hour

    return sas_token


def get_blob_full_name(blob_url: str):
    _, _, blob_name, blob_prefix, file_type = parse_azure_blob_url(blob_url)
    blob_full_name = f"{blob_name}.{file_type}"
    if blob_prefix:
        blob_full_name = f"{blob_prefix}/{blob_full_name}"
    return blob_full_name


def parse_azure_blob_url(blob_url: str):
    parsed_url = urlparse(blob_url)

    storage_account = parsed_url.netloc.split('.')[0]
    path_parts = parsed_url.path.lstrip('/').split('/')
    container_name = path_parts[0]
    blob_name_with_extension = path_parts[-1]
    blob_name = os.path.splitext(blob_name_with_extension)[0]
    blob_prefix = '/'.join(path_parts[1:-1])
    file_type = os.path.splitext(blob_name_with_extension)[1].lstrip('.')
    
    return storage_account, container_name, blob_name, blob_prefix, file_type