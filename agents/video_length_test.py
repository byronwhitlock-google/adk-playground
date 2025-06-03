"""
This script tests the `get_video_length_gcs_partial_download` function
from the `video_producer_agent.video_length_tool`.

It attempts to determine the duration of an MP4 video stored in GCS by
downloading only a partial segment of the file and using the `mutagen` library.
The test requires a valid GCS URI to an MP4 file to be specified.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from video_producer_agent.video_length_tool import get_video_length_gcs_partial_download

async def run_get_video_length_test():
    """
    Executes the get_video_length_gcs_partial_download function with test data.
    Ensures necessary environment variables are set (though not directly used by
    the function under test, they are good practice for test environments).
    The test relies on a hardcoded GCS URI for an MP4 video.
    """
    print("--- Starting Get Video Length Tool Real Execution Test ---")

    # Load environment variables from .env file (e.g., for GOOGLE_APPLICATION_CREDENTIALS)
    load_dotenv()

    # --- IMPORTANT: This GCS URI must point to an existing, valid MP4 file for the test to pass ---
    # Example: "gs://your-bucket-name/path/to/your_video.mp4"
    test_video_uri = "gs://byron-alpha-vpagent/commercials/117f74eb3a104b6fbeeaa327b99964dc.mp4"

    # --- Pre-checks for the URI format ---
    if not test_video_uri: # Should not happen with hardcoded URI, but good practice
        print("\nERROR: Test video URI is not set.")
        sys.exit(1)

    if not test_video_uri.startswith("gs://"):
        print(f"\nERROR: Invalid GCS URI format: {test_video_uri}. Must start with 'gs://'.")
        sys.exit(1)

    # The get_video_length_gcs_partial_download function now directly accepts the GCS URI.
    # Parsing of bucket_name and blob_name is handled within the function.
    print(f"Using Test Video URI: {test_video_uri}")

    # --- Execute the Function ---
    try:
        print("\nCalling get_video_length_gcs_partial_download...")
        # The function get_video_length_gcs_partial_download takes gcs_uri as its argument
        # and no longer bucket_name, blob_name, or read_bytes from the caller.
        video_length = get_video_length_gcs_partial_download(gcs_uri=test_video_uri)

        # The function returns either a float (duration) or an error string.
        if isinstance(video_length, float):
            print("\n--- Get Video Length Tool Execution Completed Successfully! ---")
            print(f"The video '{test_video_uri}' has a duration of {video_length:.2f} seconds.")
            minutes = int(video_length // 60)
            seconds = video_length % 60
            print(f"Which is {minutes} minutes and {seconds:.2f} seconds.")
        elif isinstance(video_length, str) and video_length.startswith("Error:"):
            print("\n--- Get Video Length Tool Execution FAILED (Function returned error) ---")
            print(video_length) # Print the error message from the function
        else: # Should ideally be one of the above two.
            print("\n--- Get Video Length Tool Execution FAILED (No duration returned or unexpected return type) ---")
            print(f"Returned value: {video_length}")
            print("Please check the logs above for specific errors from the function.")


    except Exception as e: # Catch any unexpected errors in the test script itself
        print(f"\n--- Get Video Length Tool Execution FAILED (Unexpected test script error) ---")
        print(f"An unexpected error occurred during test execution: {type(e).__name__} - {e}")
        print("\nPlease check the following:")
        print("  - Your Google Cloud authentication is correctly set up (e.g., GOOGLE_APPLICATION_CREDENTIALS).")
        print("  - The GCS URI is valid and accessible.")
        print("  - The video file is a valid MP4 and not corrupted.")
        print("  - The `mutagen` library is installed and working correctly.")
        sys.exit(1) 

if __name__ == "__main__":
    # This test script uses asyncio for consistency with other tests,
    # though get_video_length_gcs_partial_download itself is not async.
    # It's good practice for a test runner if other async tests exist.
    asyncio.run(run_get_video_length_test())