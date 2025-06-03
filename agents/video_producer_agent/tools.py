import re
import time

def generate_unique_gcs_uri(bucket_name: str) -> str:
    """
    Generates a a unique Google Cloud Storage (GCS) URI suitable for a final output video file.

    Args:
        bucket_name: The name of the GCS bucket.

    Returns:
        A unique GCS URI string in the format "gs://bucket_name/object_name".

    Raises:
        ValueError: If the bucket name or object name is invalid.
    """
    if not re.match(r'^[a-z0-9_.-]+$', bucket_name):
        raise ValueError("Invalid bucket name: Must contain only lowercase letters, numbers, underscores, hyphens, and periods.")

    object_name = f"output_video_{int(time.time())}.mp4"
    return f"gs://{bucket_name}/{object_name}"

def gcs_uri_to_public_url(gcs_uri: str) -> str:
    """
    Converts a Google Cloud Storage (GCS) URI to its public HTTPS URL format.

    Args:
        gcs_uri: The GCS URI string (e.g., "gs://bucket_name/object_name").

    Returns:
        The corresponding public HTTPS URL string
        (e.g., "https://storage.googleapis.com/bucket_name/object_name").

    Raises:
        ValueError: If the input string is not a valid GCS URI format
                    starting with "gs://" and containing a bucket and object name.
    """
    if not gcs_uri or not gcs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI: Must start with 'gs://'")

    # Remove the "gs://" prefix
    path_part = gcs_uri[5:]

    # Find the first slash separating bucket from object
    slash_index = path_part.find('/')

    # Check if the format is valid (must have bucket and object name)
    if slash_index == -1:
        raise ValueError("Invalid GCS URI: Format must be gs://BUCKET_NAME/OBJECT_NAME")
        # Could potentially handle gs://BUCKET_NAME separately if needed
    if slash_index == len(path_part) - 1:
         raise ValueError("Invalid GCS URI: Missing object name after bucket name /")


    # Extract bucket name and object name
    bucket_name = path_part[:slash_index]
    object_name = path_part[slash_index+1:] # Get everything after the first slash

    if not bucket_name:
        raise ValueError("Invalid GCS URI: Missing bucket name")
    # It's okay for object_name to be empty here if the URI was e.g. "gs://bucket//" but usually indicates an issue.
    # The earlier check for slash_index == len(path_part) - 1 already handles "gs://bucket/"

    # Construct the public URL using an f-string
    public_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"

    return public_url