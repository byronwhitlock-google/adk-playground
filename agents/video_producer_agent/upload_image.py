import os
import mimetypes # Standard library for MIME type guessing

# GCP SDK for storage
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
import base64
               

# --- Pure Python Image Check Helper Functions ---

def _is_image_pure_python_magic_numbers(file_path: str) -> bool:
    """
    Checks if a file is likely an image by inspecting its magic numbers.
    This is a basic check and might not cover all image types or be foolproof.
    """
    # (name, magic_bytes, offset)
    magic_signatures = [
        ("jpeg", b'\xFF\xD8\xFF', 0),
        ("png", b'\x89PNG\r\n\x1a\n', 0),
        ("gif", b'GIF8', 0), # Covers GIF87a and GIF89a
        ("bmp", b'BM', 0),
        ("tiff_le", b'II*\x00', 0),
        ("tiff_be", b'MM\x00*', 0),
        ("webp_riff", b'RIFF', 0), # Needs a secondary check for 'WEBP' at offset 8
    ]

    try:
        with open(file_path, 'rb') as f:
            header = f.read(12) # Read enough for most common headers + WEBP check
            if not header:
                # print(f"Debug: File '{file_path}' is empty (magic number check).")
                return False

            for name, magic, offset in magic_signatures:
                if len(header) >= offset + len(magic):
                    if header[offset:offset + len(magic)] == magic:
                        if name == "webp_riff": # Specific check for WEBP
                            if len(header) >= 12 and header[8:12] == b'WEBP':
                                # print(f"Debug: Magic number matched: WEBP for '{file_path}'")
                                return True
                            else:
                                continue # RIFF matched, but not WEBP
                        # print(f"Debug: Magic number matched: {name} for '{file_path}'")
                        return True
            # print(f"Debug: No known image magic numbers matched for '{file_path}'. Header (first 12 bytes): {header.hex()}")
            return False
    except IOError as e:
        print(f"Error: Could not read file {file_path} for magic number check: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during magic number check for {file_path}: {e}")
        return False

def _is_image_mimetype(file_path: str) -> bool:
    """
    Checks if a file is an image based on its MIME type using the 'mimetypes' module.
    """
    if not os.path.exists(file_path):
        # print(f"Debug: File not found at {file_path} for mimetype check.")
        return False
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype:
        # print(f"Debug: Guessed mimetype for '{file_path}': {mimetype}")
        if mimetype.startswith('image/'):
            return True
        # Explicitly check common image mimetypes as a fallback
        if mimetype in ['image/jpeg', 'image/png']: # only support these types
            return True
    # print(f"Debug: Mimetype for '{file_path}' ('{mimetype}') is not recognized as a common image type.")
    return False

# --- Main Processing Function ---

def store_image_artifact_in_gcs(
    local_artifact_path: str,
    gcs_destination_blob_prefix: str = "agent_image_uploads/"
) -> str: # Return type is now consistently str (either URI or error message)
    """
    Processes a local artifact: checks if it's an image using pure Python methods,
    and if so, uploads it to Google Cloud Storage. only supports jpeg and png.

    Args:
        local_artifact_path (str): The local file path to the artifact.
        gcs_destination_blob_prefix (str, optional): A prefix (folder path) to use
                                                     within the GCS bucket.
                                                     Defaults to "agent_image_uploads/".

    Returns:
        str: The GCS URI (gs://bucket/blob_name) of the uploaded image if successful,
             OR a string describing the error if any part of the process fails.
    """
    print(f"Processing artifact: '{local_artifact_path}'")
    error_prefix = "Error: "

    # --- Validate local artifact path ---
    if not os.path.exists(local_artifact_path):
        error_msg = f"Artifact file not found at '{local_artifact_path}'."
        print(error_prefix + error_msg)
        return error_prefix + error_msg
    if not os.path.isfile(local_artifact_path):
        error_msg = f"Artifact path '{local_artifact_path}' is not a file."
        print(error_prefix + error_msg)
        return error_prefix + error_msg
    if os.path.getsize(local_artifact_path) == 0:
        error_msg = f"Artifact file '{local_artifact_path}' is empty."
        print(error_prefix + error_msg)
        return error_prefix + error_msg

    # --- Image Verification (Pure Python methods) ---
    print(f"Verifying if '{local_artifact_path}' is an image...")
    is_image = False
    if _is_image_mimetype(local_artifact_path):
        print(f"'{local_artifact_path}' identified as an image by mimetype.")
        is_image = True
    else:
        print(f"Mimetype check did not identify '{local_artifact_path}' as an image. Attempting magic number check.")
        if _is_image_pure_python_magic_numbers(local_artifact_path):
            print(f"'{local_artifact_path}' identified as an image by magic numbers.")
            is_image = True

    if not is_image:
        error_msg = f"File '{local_artifact_path}' is not recognized as a valid image type by pure Python checks."
        print(error_prefix + error_msg)
        return error_prefix + error_msg

    # --- GCS Configuration and Client Initialization ---
    gcs_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET")
    gcp_project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not gcs_bucket_name:
        error_msg = "GOOGLE_CLOUD_BUCKET environment variable is not set. Cannot upload to GCS."
        print(error_prefix + error_msg)
        return error_prefix + error_msg

    try:
        storage_client = storage.Client(project=gcp_project_id if gcp_project_id else None)
    except DefaultCredentialsError:
        error_msg = (
            "Google Cloud Default Credentials not found. "
            "Ensure you are authenticated (e.g., `gcloud auth application-default login` "
            "or service account key is set via GOOGLE_APPLICATION_CREDENTIALS)."
        )
        print(error_prefix + error_msg)
        return error_prefix + error_msg
    except Exception as e:
        error_msg = f"Failed to initialize Google Cloud Storage client: {e}"
        print(error_prefix + error_msg)
        return error_prefix + error_msg

    # --- Prepare GCS Destination ---
    file_name = os.path.basename(local_artifact_path)
    
    # Ensure prefix ends with a slash if it's not empty
    if gcs_destination_blob_prefix and not gcs_destination_blob_prefix.endswith('/'):
        prefix_to_use = f"{gcs_destination_blob_prefix}/"
    elif not gcs_destination_blob_prefix: # Handle empty prefix
        prefix_to_use = ""
    else:
        prefix_to_use = gcs_destination_blob_prefix
        
    destination_blob_name = f"{prefix_to_use}{file_name}"
    
    # Clean up potential double slashes if prefix was empty or just "/"
    destination_blob_name = destination_blob_name.replace('//', '/')
    if destination_blob_name.startswith('/'): # Should not happen if prefix is handled correctly
        destination_blob_name = destination_blob_name[1:]


    # --- Upload to GCS ---
    try:
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(destination_blob_name)

        print(f"Attempting to upload '{local_artifact_path}' to 'gs://{gcs_bucket_name}/{destination_blob_name}'...")
        blob.upload_from_filename(local_artifact_path)
        gcs_uri = f"gs://{gcs_bucket_name}/{destination_blob_name}"
        print(f"File '{local_artifact_path}' uploaded successfully to '{gcs_uri}'.")
        return gcs_uri # Success: return GCS URI
    except Exception as e:
        error_msg = f"Uploading file '{local_artifact_path}' to GCS bucket '{gcs_bucket_name}' failed: {e}"
        print(error_prefix + error_msg)
        return error_prefix + error_msg # Failure: return error string
