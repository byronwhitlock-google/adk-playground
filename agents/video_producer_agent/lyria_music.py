import base64
import google.auth
import google.auth.transport.requests
import requests
import os
import uuid # For generating unique filenames
from typing import Dict, Optional, Union # Union will be resolved to str effectively

from dotenv import load_dotenv # For implicitly loading .env file
from google.cloud import storage # For GCS upload

# Load environment variables from .env file if it exists
load_dotenv()

# --- Helper function (no changes needed here) ---
def _send_request_to_google_api(api_endpoint: str, access_token: str, data: Optional[Dict] = None) -> Dict:
    """Sends an HTTP request to a Google API endpoint. Can raise requests.exceptions.RequestException."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    # This can raise various requests.exceptions.RequestException (e.g., ConnectionError, Timeout)
    response = requests.post(api_endpoint, headers=headers, json=data)
    # This will raise HTTPError for bad responses (4xx or 5xx)
    response.raise_for_status()
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        # This case handles 200 OK but with malformed JSON, re-raise to be caught in main func
        raise ValueError(f"API returned 200 OK but with invalid JSON: {e}. Response text: {response.text[:500]}")


# --- Main function to generate a single WAV music file and upload to GCS ---
def generate_lyria_music(
    prompt: str,
    negative_prompt: str # Optional str
) -> str: # Returns GCS URI (str) or an error message (str)
    """
    Generates a single WAV music file using Lyria, uploads it to GCS,
    and returns its GCS URI string or an error message string.
    Audio length per clip	30 seconds
    
    Examples of prompts: 
    - For Genre and Style use A cinematic orchestral piece in a heroic, fantasy adventure style, with a grand, sweeping melody.
    - For Mood and Instrumentation use A peaceful and serene acoustic guitar piece, featuring a fingerpicked style, perfect for meditation.
    - For Tempo and Rhythm use	A tense, suspenseful underscore with a very slow, creeping tempo and a sparse, irregular rhythm. Primarily uses low strings and subtle percussion.

    Args:
        prompt: A detailed description of the music to generate.
        negative_prompt: (Optional) Description of what to exclude.
        
    """

    # --- Resolve configuration from environment variables ---
    resolved_project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    # Using GOOGLE_CLOUD_LOCATION for consistency if preferred, or stick to LYRIA_LOCATION
    resolved_location = os.getenv("GOOGLE_CLOUD_LOCATION", os.getenv("LYRIA_LOCATION", "us-central1"))
    resolved_model_id = os.getenv("LYRIA_MODEL_ID", "lyria-002")
    gcs_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent") # As per user's last snippet

    if not resolved_project_id:
        return "ERROR: GOOGLE_CLOUD_PROJECT environment variable must be set."
    if not gcs_bucket_name:
        return "ERROR: GOOGLE_CLOUD_BUCKET environment variable must be set for Lyria output."
    if not prompt:
        return "ERROR: A 'prompt' is required."
    
    # --- 1. Authentication (for Lyria API) ---
    access_token: Optional[str] = None
    try:
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        access_token = creds.token
        if not access_token: # Should not happen if creds.refresh succeeded without error
            return "ERROR: Failed to obtain access token after credential refresh."
    except google.auth.exceptions.DefaultCredentialsError:
        return "ERROR: Google Cloud ADC not found. Run 'gcloud auth application-default login'."
    except google.auth.exceptions.RefreshError as e:
        return f"ERROR: Could not refresh access token: {e}."
    except Exception as e_auth: # Catch any other unexpected auth errors
        return f"ERROR: An unexpected authentication error occurred: {e_auth}."


    # --- 2. Construct Lyria API Endpoint ---
    api_endpoint = (
        f"https://{resolved_location}-aiplatform.googleapis.com/v1/projects/{resolved_project_id}"
        f"/locations/{resolved_location}/publishers/google/models/{resolved_model_id}:predict"
    )

    # --- 3. Prepare Lyria request payload ---
    instance_payload: Dict[str, Union[str, int]] = {"prompt": prompt}
    if negative_prompt: instance_payload["negative_prompt"] = negative_prompt


    request_body = {"instances": [instance_payload], "parameters": {}}
    print(f"Sending request to Lyria model: {request_body} at {api_endpoint}")

    # --- 4. Send request to the Lyria API ---
    response_json: Optional[Dict] = None
    try:
        response_json = _send_request_to_google_api(api_endpoint, access_token, request_body)
    except requests.exceptions.HTTPError as e_http:
        error_message = f"Lyria API HTTP Error: {e_http}."
        if e_http.response is not None:
            try:
                error_message += f" Response content: {e_http.response.text[:1000]}" # Limit response text length
            except Exception:
                error_message += " Could not decode response content."
        print(error_message)
        return error_message
    except requests.exceptions.RequestException as e_req: # Catches other network/request issues
        error_message = f"Lyria API Request Failed (e.g., network issue): {e_req}."
        print(error_message)
        return error_message
    except ValueError as e_json_decode: # Catches JSONDecodeError from helper or other ValueErrors
        error_message = f"Error processing Lyria API response (likely JSON decoding): {e_json_decode}."
        print(error_message)
        return error_message
    except Exception as e_unexpected_api: # Fallback for truly unexpected errors in API call
        error_message = f"An unexpected error occurred during Lyria API call: {e_unexpected_api}."
        print(error_message)
        return error_message

    # --- 5. Initialize GCS Client ---
    try:
        storage_client = storage.Client(project=resolved_project_id)
        bucket = storage_client.bucket(gcs_bucket_name)
    except Exception as e_gcs_client:
        return f"ERROR: Failed to initialize GCS client or bucket '{gcs_bucket_name}': {e_gcs_client}."

    # --- 6. Process first prediction, save WAV locally, upload to GCS, and cleanup ---
    if not response_json or "predictions" not in response_json or not response_json["predictions"]:
        return "ERROR: API response did not contain 'predictions' or predictions list is empty."

    pred_data = response_json["predictions"][0] # Process only the first prediction

    if "bytesBase64Encoded" not in pred_data:
        return "ERROR: First prediction from API is missing 'bytesBase64Encoded' data."
    
    bytes_b64 = pred_data["bytesBase64Encoded"]
    try:
        decoded_wav_data = base64.b64decode(bytes_b64)
    except base64.binascii.Error as e_decode:
        return f"ERROR: Failed to decode base64 audio data from API prediction: {e_decode}."

    local_wav_filename = f"lyria_output_{uuid.uuid4()}.wav"
    blob_name = local_wav_filename
    gcs_uri_result: Optional[str] = None

    try:
        # a. Save decoded WAV data locally
        with open(local_wav_filename, "wb") as out_wav:
            out_wav.write(decoded_wav_data)
        print(f"Audio content temporarily written to: '{local_wav_filename}'")

        # b. Upload local WAV to GCS
        blob = bucket.blob(blob_name)
        print(f"Uploading '{local_wav_filename}' to GCS bucket '{gcs_bucket_name}'...")
        blob.upload_from_filename(local_wav_filename, content_type='audio/wav')
        gcs_uri_result = f"gs://{gcs_bucket_name}/{blob_name}"
        print(f"✅ Audio successfully uploaded to GCS: {gcs_uri_result}")

        # c. Clean up local WAV file (after successful upload)
        try:
            os.remove(local_wav_filename)
            print(f"Local WAV file '{local_wav_filename}' removed.")
        except OSError as e_remove:
            # Log/print warning but still return success URI as upload was successful
            print(f"WARNING: Upload to {gcs_uri_result} Succeeded, BUT failed to remove local file '{local_wav_filename}': {e_remove}.")
        
        return gcs_uri_result # Success path

    except Exception as e_main_op: # Covers local write or GCS upload errors
        # Attempt to clean up local file if it exists, even on failure
        if os.path.exists(local_wav_filename):
            try:
                os.remove(local_wav_filename)
                print(f"Cleaned up local file '{local_wav_filename}' after error: {e_main_op}.")
            except OSError as e_rem_on_fail:
                print(f"WARNING: Failed to remove local file '{local_wav_filename}' after an error during main operation: {e_rem_on_fail}")
        return f"ERROR during local file write or GCS upload: {e_main_op}."

    # Fallback - This should ideally not be reached if all paths are covered.
    return "ERROR: An unknown error occurred after processing predictions."

