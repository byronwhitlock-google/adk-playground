# test_get_video_length.py
import asyncio
import os
import sys
from dotenv import load_dotenv
from video_producer_agent.video_length_tool import get_video_length_gcs_partial_download

async def run_get_video_length_test():
    """
    Executes the get_video_length_gcs_partial_download function with test data.
    Ensures necessary environment variables are set.
    """
    print("--- Starting Get Video Length Tool Real Execution Test ---")

    # --- Configuration ---
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve configuration from environment variables (set in .env or your shell)
    # GOOGLE_CLOUD_PROJECT is often implicitly used by google-cloud-storage if authenticated
    # but good practice to check if you need it for other GCP APIs.
    # project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    # --- IMPORTANT: Replace with your actual GCS URIs for testing ---
    # Ensure this video file exists in your GCS bucket and is an MP4.
    # Example: "gs://your-bucket-name/path/to/your_video.mp4"
    test_video_uri =  "gs://byron-alpha-vpagent/commercials/117f74eb3a104b6fbeeaa327b99964dc.mp4"

    # --- Pre-checks ---
    if not test_video_uri:
        print("\nERROR: 'TEST_VIDEO_URI' environment variable is not set.")
        print("Please ensure it's defined in your .env file or your environment.")
        print("Example: TEST_VIDEO_URI=\"gs://your-bucket-name/path/to/your_video.mp4\"")
        sys.exit(1)

    # Parse bucket name and blob name from the GCS URI
    if not test_video_uri.startswith("gs://"):
        print(f"\nERROR: Invalid GCS URI format: {test_video_uri}. Must start with 'gs://'.")
        sys.exit(1)

    uri_parts = test_video_uri[5:].split('/', 1) # Remove 'gs://' and split once
    if len(uri_parts) < 2:
        print(f"\nERROR: Invalid GCS URI format: {test_video_uri}. Missing blob name.")
        sys.exit(1)
    
    bucket_name = uri_parts[0]
    blob_name = uri_parts[1]

    print(f"Using Test Video URI: {test_video_uri}")
    print(f"  Bucket: {bucket_name}")
    print(f"  Blob: {blob_name}")

    # --- Execute the Function ---
    try:
        print("\nCalling get_video_length_gcs_partial_download...")
        video_length = get_video_length_gcs_partial_download(
            bucket_name=bucket_name,
            blob_name=blob_name,
            read_bytes=5 * 1024 * 1024 # Try with 5MB for MP4
        )

        if video_length is not None:
            print("\n--- Get Video Length Tool Execution Completed Successfully! ---")
            print(f"The video '{test_video_uri}' has a duration of {video_length:.2f} seconds.")
            minutes = int(video_length // 60)
            seconds = video_length % 60
            print(f"Which is {minutes} minutes and {seconds:.2f} seconds.")
        else:
            print("\n--- Get Video Length Tool Execution FAILED (No duration returned) ---")
            print("Please check the logs above for specific errors.")

    except Exception as e:
        print(f"\n--- Get Video Length Tool Execution FAILED ---")
        print(f"An unexpected error occurred during test execution: {type(e).__name__} - {e}")
        print("\nPlease check the following:")
        print("  - Your Google Cloud authentication is correctly set up (e.g., GOOGLE_APPLICATION_CREDENTIALS).")
        print("  - The GCS URI in TEST_VIDEO_URI is valid and accessible.")
        print("  - The video file is a valid MP4.")
        print("  - FFmpeg is installed and accessible in your system's PATH.")
        sys.exit(1) # Exit with an error code on failure

if __name__ == "__main__":
    # This test script uses asyncio for consistency with the mux_test.py,
    # though get_video_length_gcs_partial_download itself is not async.
    # It's good practice for a test runner.
    asyncio.run(run_get_video_length_test())