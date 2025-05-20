import os
from google.cloud import storage
from google.cloud.exceptions import NotFound
from moviepy.editor import VideoFileClip
from moviepy.tools import ffmpeg_parse_infos # Potentially useful for deeper introspection
import tempfile
import logging

# Configure logging for better error reporting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_length_gcs_partial_download(bucket_name: str, blob_name: str, read_bytes: int = 5 * 1024 * 1024) -> float | None:
    """
    Gets the duration of an MP4 video stored in a GCS bucket by downloading
    only the initial portion of the file. This is efficient for MP4s where
    metadata (including duration) is typically at the beginning.

    Args:
        blob_name (str): The full path to the video file within the bucket
                         (e.g., 'videos/my_video.mp4').
        read_bytes (int): The number of bytes to download from the beginning
                          of the video file. 5MB is often sufficient for MP4 metadata.

    Returns:
        float: The duration of the video in seconds, or None if an error occurs.
    """
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    temp_file_path = None # Initialize to None for finally block

    try:
        # --- Step 1: Check if the bucket and blob exist ---
        try:
            # Reload attributes to get the latest metadata, including size
            blob.reload()
            logging.info(f"Blob '{blob_name}' found in bucket '{bucket_name}'. Size: {blob.size / (1024 * 1024):.2f} MB")
        except NotFound:
            logging.error(f"Error: Blob '{blob_name}' not found in bucket '{bucket_name}'. Please check the name and path.")
            return None
        except Exception as e:
            logging.error(f"Error checking blob existence for '{blob_name}': {e}")
            return None

        file_size = blob.size
        # Adjust read_bytes if the file is smaller than the requested read_bytes
        bytes_to_read = min(read_bytes, file_size)

        # --- Step 2: Create a temporary file and download a portion ---
        # We use a temporary file because moviepy/ffmpeg often need a file path
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(blob_name)[1], delete=False) as temp_video_file:
            temp_file_path = temp_video_file.name

        logging.info(f"Attempting to download first {bytes_to_read / (1024 * 1024):.2f} MB of '{blob_name}' to temporary file: {temp_file_path}")
        
        # Download only a range of bytes
        blob.download_to_filename(temp_file_path, start_byte=0, end_byte=bytes_to_read - 1)
        logging.info("Partial download complete.")

        # --- Step 3: Analyze the partial file with moviepy ---
        logging.info(f"Analyzing partial video file: {temp_file_path}")
        
        clip = None # Initialize clip to None
        try:
            clip = VideoFileClip(temp_file_path)
            duration = clip.duration
            logging.info(f"Successfully extracted video duration: {duration} seconds")
            return duration
        except Exception as e:
            logging.error(f"Error extracting duration using moviepy from partial file: {e}")
            logging.warning("This might happen if the video metadata (moov atom) is not in the downloaded portion, "
                            "or if the partial file is not parsable by ffmpeg/moviepy.")
            logging.warning(f"Consider increasing 'read_bytes' (current: {read_bytes / (1024 * 1024):.2f} MB) or checking the MP4's 'faststart' status.")
            return None

    except NotFound as e:
        # This specific NotFound handles cases where the bucket itself might not exist
        logging.error(f"Error: Bucket '{bucket_name}' not found. Details: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during the process
        logging.error(f"An unexpected error occurred: {e}", exc_info=True) # exc_info=True prints traceback
        return None
    finally:
        # --- Step 4: Clean up the temporary file ---
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logging.info(f"Temporary partial file '{temp_file_path}' deleted.")
            except Exception as e:
                logging.error(f"Error deleting temporary file '{temp_file_path}': {e}")
        
        # Ensure the clip object is closed if it was opened
        if clip:
            try:
                clip.close()
            except Exception as e:
                logging.error(f"Error closing moviepy clip: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # IMPORTANT: Replace with your actual GCS bucket name and video file path
    # For testing, ensure this video is an MP4 and is accessible by your credentials.
    your_bucket_name = "your-gcs-bucket-name"
    your_video_blob_name = "your-video-folder/your_video.mp4" # Example: "videos/sample.mp4"

    # --- Test Cases ---
    print("\n--- Test Case 1: Valid MP4 Video ---")
    video_length = get_video_length_gcs_partial_download(your_bucket_name, your_video_blob_name)

    if video_length is not None:
        print(f"The video '{your_video_blob_name}' has a duration of {video_length:.2f} seconds.")
        minutes = int(video_length // 60)
        seconds = video_length % 60
        print(f"Which is {minutes} minutes and {seconds:.2f} seconds.")
    else:
        print("Could not determine video length for the valid test case.")

    print("\n--- Test Case 2: Non-existent Blob ---")
    non_existent_blob = "non-existent-folder/non_existent_video.mp4"
    get_video_length_gcs_partial_download(your_bucket_name, non_existent_blob)

    print("\n--- Test Case 3: Non-existent Bucket (will likely raise NotFound earlier) ---")
    non_existent_bucket = "this-bucket-does-not-exist-12345"
    # This might fail earlier depending on GCS client's eager validation
    get_video_length_gcs_partial_download(non_existent_bucket, your_video_blob_name)

    # You can add more test cases, e.g., with a very small read_bytes that might fail
    # print("\n--- Test Case 4: Insufficient read_bytes (might fail if metadata is larger) ---")
    # get_video_length_gcs_partial_download(your_bucket_name, your_video_blob_name, read_bytes=10 * 1024) # 10 KB