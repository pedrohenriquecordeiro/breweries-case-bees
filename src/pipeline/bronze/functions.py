from google.cloud import storage
import json , logging, os



def load_metadata():
    
    """
    Loads metadata from a Google Cloud Storage (GCS) bucket.

    This function connects to a GCS bucket specified by the BUCKET_NAME environment variable,
    retrieves the 'bronze/_metadata/metadata.json' file and parses its contents as JSON.
    If the metadata cannot be loaded for any reason, an empty dictionary is returned.

    Returns:
        dict: The metadata loaded from the JSON file, or an empty dictionary if loading fails.

    Logs:
        - Info message when metadata is successfully loaded.
        - Warning message if loading fails, including the exception details.
    """
    
    try:
        client = storage.Client()
        bucket = client.get_bucket(os.environ["BUCKET_NAME"])
        blob = bucket.blob("bronze/_metadata/metadata.json")
    
        data = blob.download_as_text()
        logging.info("Loaded metadata from GCS.")
        return json.loads(data)
    
    except Exception as e:
        logging.warning(f"Could not load metadata: {e}")
        return {}



def save_metadata(metadata: dict):
    
    """
    Save metadata dictionary as a JSON file to a specified Google Cloud Storage bucket.

    Args:
        metadata (dict): The metadata to be saved.

    Raises:
        google.cloud.exceptions.GoogleCloudError: If there is an error uploading the metadata to the bucket.

    Environment Variables:
        BUCKET_NAME: The name of the Google Cloud Storage bucket where the metadata will be saved.

    Logs:
        Logs an info message upon successful save of the metadata.
    """
    
    try:
        client = storage.Client()
        bucket = client.get_bucket(os.environ["BUCKET_NAME"])
        blob   = bucket.blob("bronze/_metadata/metadata.json")
        blob.upload_from_string(json.dumps(metadata, indent = 2), content_type = "application/json")
        
        logging.info(f"Saved metadata: {metadata}")
        
    except Exception as e:
        logging.error(f"Could not save metadata: {e}")
        raise e


def save_file_to_gcs(data: dict, path: str = "bronze"):
    
    """
    Saves a dictionary as a JSON file to a Google Cloud Storage (GCS) bucket.

    Args:
        data (dict): The data to be saved as a JSON file.
        path (str, optional): The prefix or path in the GCS bucket where the file will be saved. Defaults to "bronze".

    Raises:
        google.cloud.exceptions.GoogleCloudError: If there is an error uploading the file to GCS.

    Environment Variables:
        BUCKET_NAME: The name of the GCS bucket where the file will be saved.

    Logs:
        Logs an info message indicating the file has been saved to GCS.
    """
    
    try:
        client = storage.Client()
        bucket = client.get_bucket(os.environ["BUCKET_NAME"])
        blob   = bucket.blob(path)
        blob.upload_from_string(json.dumps(data, indent = 2), content_type = "application/json")
        
        logging.info(f"Saved file to GCS at {path}.")
    except Exception as e:
        logging.error(f"Could not save file to GCS: {e}")
        raise e