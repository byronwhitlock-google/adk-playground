import re

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

# --- Example Usage ---
gcs_video_uri = "gs://byron-alpha-vpagent/3208593487945471240/sample_0.mp4"

try:
    http_video_url = gcs_uri_to_public_url(gcs_video_uri)
    # print(f"GCS URI: {gcs_video_uri}")
    # print(f"Public URL: {http_video_url}")

    # Example with nested folders in object name
    gcs_nested_uri = "gs://my-cool-bucket/data/videos/archive/vid_001.mp4"
    http_nested_url = gcs_uri_to_public_url(gcs_nested_uri)
    # print(f"\nGCS URI: {gcs_nested_uri}")
    # print(f"Public URL: {http_nested_url}")

except ValueError as e:
    print(f"Error: {e}")

# --- Note on your provided return statement ---
# The return statement you included in your request:
# return f"gs://{bucket_name}/{object_name}"
# actually performs the *reverse* operation (converting components back to a GCS URI).
# The function above implements the conversion described in your text and example.