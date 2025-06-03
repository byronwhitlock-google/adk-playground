import os
from google.cloud import storage
from google.cloud.exceptions import NotFound
import tempfile
import logging
from mutagen.mp4 import MP4, MP4StreamInfoError # For MP4 parsing
from urllib.parse import urlparse

def get_duration_with_mutagen(file_path: str) -> float:
    """
    Uses the mutagen library to get the duration of an MP4 file.

    Args:
        file_path (str): Path to the MP4 file.

    Returns:
        float: Duration in seconds, or None if an error occurs.
    """
    try:
        video = MP4(file_path)
        if video.info:
            duration_seconds = video.info.length
            print(f"Mutagen: Extracted duration: {duration_seconds:.2f}s")
            return duration_seconds
        else:
            print(f"Mutagen: Could not retrieve info object for {file_path}")
            return None
    except MP4StreamInfoError as e:
        # This specific error can occur if mutagen can't find essential metadata,
        # often because the 'moov' atom is missing or not where expected in a partial file.
        print(f"Mutagen: MP4StreamInfoError for '{file_path}': {e}. "
                        "This often means the 'moov' atom (metadata) was not found in the downloaded portion.")
        return None
    except Exception as e:
        print(f"Mutagen: An error occurred while processing '{file_path}': {e}", exc_info=True)
        return None

def parse_gcs_uri(gcs_uri: str) -> tuple[str, str] | None:
    """
    Parses a GCS URI (gs://bucket-name/object-name) into bucket name and object name.

    Args:
        gcs_uri (str): The GCS URI.

    Returns:
        tuple[str, str] | None: A tuple containing (bucket_name, blob_name)
                                 or None if the URI is invalid.
    """
    parsed_url = urlparse(gcs_uri)
    if parsed_url.scheme == "gs" and parsed_url.netloc and parsed_url.path:
        bucket_name = parsed_url.netloc
        blob_name = parsed_url.path.lstrip('/')
        return bucket_name, blob_name
    return None

def get_video_length_gcs_partial_download(gcs_uri: str ) -> str :
    """
    Gets the duration of an MP4 video stored in a GCS bucket by downloading
    only the initial portion of the file and using the 'mutagen' library.

    Args:
        gcs_uri (str): The GCS URI of the video file (e.g., 'gs://my-bucket/videos/my_video.mp4').
        read_bytes (int): The number of bytes to download from the beginning
                          of the video file. 1MB is used by default.

    Returns:
        str: The duration of the video in (float)seconds, or an error message if an error occurs.
    """
    read_bytes = 1 * 1024 * 1024  # 1MB

    parsed_uri = parse_gcs_uri(gcs_uri)
    if not parsed_uri:
        return f"Error: Invalid GCS URI format: '{gcs_uri}'. Expected 'gs://bucket-name/object-name'."

    bucket_name, blob_name = parsed_uri

    if not blob_name: # Handle cases like gs://bucket-name/
        return f"Error: No object name specified in GCS URI: '{gcs_uri}'."

    storage_client = storage.Client()
    temp_file_path = None

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        try:
            blob.reload() # Check if blob exists and get metadata
            print(f"Blob '{blob_name}' found in bucket '{bucket_name}'. Size: {blob.size / (1024 * 1024):.2f} MB")
        except NotFound:
            return f"Error: Blob '{blob_name}' not found in bucket '{bucket_name}' (from URI '{gcs_uri}')."
        except Exception as e:
            return f"Error checking blob existence for '{blob_name}' in bucket '{bucket_name}': {e}"

        file_size = blob.size
        if file_size == 0:
            return f"Blob '{blob_name}' in bucket '{bucket_name}' is empty (0 bytes). Cannot determine duration."

        bytes_to_read = min(read_bytes, file_size)
        if bytes_to_read < read_bytes and file_size > 0:
             print(f"File size ({bytes_to_read / (1024*1024):.2f} MB) is smaller than requested read_bytes ({read_bytes / (1024*1024):.2f} MB). Reading available portion.")

        file_suffix = os.path.splitext(blob_name)[1] if os.path.splitext(blob_name)[1] else ".mp4"
        with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as temp_video_file:
            temp_file_path = temp_video_file.name

        print(f"Attempting to download first {bytes_to_read / (1024 * 1024):.2f} MB of '{blob_name}' from bucket '{bucket_name}' to {temp_file_path}")

        blob.download_to_filename(temp_file_path, start=0, end=bytes_to_read - 1)
        print("Partial download complete.")

        print(f"Analyzing partial video file with mutagen: {temp_file_path}")
        duration = get_duration_with_mutagen(temp_file_path)

        if duration is not None:
            print(f"Successfully extracted video duration using mutagen: {duration} seconds for GCS URI '{gcs_uri}'")
            return duration
        else:
            return (f"Could not extract duration using mutagen from the downloaded portion of '{gcs_uri}'. "
                    "This might happen if the 'moov' atom (with essential metadata) is not within the "
                    f"first {bytes_to_read / (1024 * 1024):.2f} MB, or the file is corrupted/not a supported MP4 variant.")

    except NotFound: # This would typically catch bucket not found if storage_client.bucket() fails earlier
        return f"Error: Bucket '{bucket_name}' (from URI '{gcs_uri}') not found."
    except Exception as e:
        return f"An unexpected error occurred in get_video_length_gcs_partial_download for URI '{gcs_uri}': {e}"
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Temporary partial file '{temp_file_path}' deleted.")
            except Exception as e:
                print(f"Error deleting temporary file '{temp_file_path}': {e}")
