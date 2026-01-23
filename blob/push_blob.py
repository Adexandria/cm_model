from azure.storage.blob import BlobServiceClient
import os   
import dotenv
import json

dotenv.load_dotenv()   

blob_service_client = BlobServiceClient.from_connection_string(
    os.environ["AZURE_STORAGE_CONNECTION_STRING"]
)

blob_url = os.environ["AZURE_STORAGE_URL"]
container_client = blob_service_client.get_container_client("image")

secured_container_client = blob_service_client.get_container_client("reports")

def upload_blob(report, blob_name="report.json"):
    """Uploads a JSON report to Azure Blob Storage and returns the blob URL."""
    blob_client = container_client.get_blob_client(blob_name)

    blob_client.upload_blob(
        json.dumps(report),
        overwrite=True,
        content_type="application/json"
    )
    return blob_client.url

def upload_secured_blob(report, blob_name="report.json"):
    """Uploads a JSON report to a secured Azure Blob Storage container and returns the blob URL."""
    blob_client = secured_container_client.get_blob_client(blob_name)

    blob_client.upload_blob(
        json.dumps(report),
        overwrite=True,
        content_type="application/json"
    )
    return blob_client.url