import requests
import os
import logging
import time
from datetime import datetime

try:
    from bronze.functions import load_metadata, save_metadata, save_file_to_gcs
except ImportError:
    try:
        from pipeline.bronze.functions import load_metadata, save_metadata, save_file_to_gcs
    except ImportError:
        from functions import load_metadata, save_metadata, save_file_to_gcs

from airflow.decorators import task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Configuration constants
MAX_PAGES = 1000  # Safety limit to prevent infinite loops
API_TIMEOUT = 30  # Timeout in seconds for API requests
MAX_RETRIES = 3   # Maximum retry attempts for failed requests


def fetch_breweries_page(url, page, per_page, retry_count=0):
    """
    Fetch a single page of breweries with retry logic.
    
    Args:
        url: API endpoint URL
        page: Page number to fetch
        per_page: Number of items per page
        retry_count: Current retry attempt (internal use)
    
    Returns:
        List of breweries or empty list on failure
    """
    try:
        params = {"page": page, "per_page": per_page}
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        if retry_count < MAX_RETRIES:
            wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
            logging.warning(f"Request failed (attempt {retry_count + 1}/{MAX_RETRIES}): {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return fetch_breweries_page(url, page, per_page, retry_count + 1)
        else:
            logging.error(f"Failed to fetch page {page} after {MAX_RETRIES} attempts: {e}")
            raise


@task(task_id="bronze_task")
def run_bronze_pipeline():
    os.environ["BUCKET_NAME"] = "bees-storage"

    # ------------------------------------------------------------------------------
    # CURRENT TIMESTAMP
    # ------------------------------------------------------------------------------
    CURRENT_TIMESTAMP = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")

    # ------------------------------------------------------------------------------
    # Load metadata for incremental/full load decision
    # ------------------------------------------------------------------------------
    max_id = load_metadata().get("max_id", None)

    # ------------------------------------------------------------------------------
    # INCREMENTAL LOAD
    # ------------------------------------------------------------------------------
    if max_id:
        logging.info("Starting incremental load.")
        
        per_page = 50
        url = "https://api.openbrewerydb.org/v1/breweries?sort=id:desc"
        
        # Use bounded loop instead of while True
        for page_number in range(1, MAX_PAGES + 1):
            logging.info(f"Requesting page {page_number}.")
            
            # Fetch breweries from the API
            breweries = fetch_breweries_page(url, page_number, per_page)
            
            # Filter new breweries by id
            new_breweries = [brewery for brewery in breweries if brewery['id'] > max_id]
            
            logging.info(f"The last processed id is {max_id}.")
            logging.info(f"Found {len(new_breweries)} new breweries.")
            
            if new_breweries:
                # Save new breweries to GCS
                save_file_to_gcs(
                    new_breweries,
                    f'bronze/data/{CURRENT_TIMESTAMP}/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}.json'
                )
                
                # Update metadata with new max_id
                save_metadata({
                    "max_id": max(brewery['id'] for brewery in new_breweries),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # No new breweries found, end the loop
                logging.info("No new breweries found. Incremental load complete.")
                break
        else:
            # Loop completed without break (reached MAX_PAGES)
            logging.warning(f"Reached maximum page limit ({MAX_PAGES}) during incremental load.")
    
    # ------------------------------------------------------------------------------
    # FULL LOAD (run only for the first time)
    # ------------------------------------------------------------------------------
    else:
        logging.info("Starting full load.")
        
        max_id_temporary = None
        per_page = 200
        url = "https://api.openbrewerydb.org/v1/breweries?sort=id:asc"
        
        # Use bounded loop instead of while True
        for page_number in range(1, MAX_PAGES + 1):
            logging.info(f"Requesting page {page_number}.")
            
            # Fetch breweries from the API
            breweries = fetch_breweries_page(url, page_number, per_page)
            
            if not breweries:
                # No more breweries found, save metadata and end the loop
                save_metadata({
                    "max_id": max_id_temporary,
                    "timestamp": datetime.now().isoformat()
                })
                logging.info("Full load complete.")
                break
            
            # Save breweries to GCS
            save_file_to_gcs(
                breweries,
                f'bronze/data/{CURRENT_TIMESTAMP}/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")}.json'
            )
            
            # Update max_id_temporary with highest id from current page
            max_id_temporary = max(brewery['id'] for brewery in breweries)
        else:
            # Loop completed without break (reached MAX_PAGES)
            logging.warning(f"Reached maximum page limit ({MAX_PAGES}) during full load.")
            if max_id_temporary:
                save_metadata({
                    "max_id": max_id_temporary,
                    "timestamp": datetime.now().isoformat()
                })
