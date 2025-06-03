"""
This script tests the video joining functionality of the `video_join_tool`.

It attempts to join a list of specified MP4 files from GCS using the
Transcoder API via the `video_join_tool`.
The test requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment
variables to be set, and the specified GCS input URIs must exist.
"""
import asyncio
import os
import sys 

from video_producer_agent.video_join_tool import video_join_tool
from dotenv import load_dotenv


async def main():
    """
    Main function to test the video_join_tool.
    It loads environment variables, sets up test parameters, and calls the tool.
    """
    # --- Configuration ---
    # Load .env from project root. This will set GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION etc.
    # if they are defined in a .env file.
    load_dotenv() 

    # Example parameters for the video_join_tool
    # GOOGLE_CLOUD_LOCATION is used by video_join_tool for the Transcoder job.
    test_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") 

    # --- IMPORTANT: These GCS URIs must point to existing, valid MP4 files for the test to pass ---
    test_input_uris = [
        "gs://byron-alpha-vpagent/muxed_audio_output/muxed_output_1747264766.mp4",
        # The following URI is commented out as it's noted to have no audio, 
        # which might be relevant depending on the video_join_tool's behavior with such files.
        # "gs://byron-alpha-vpagent/10717361122161337346/sample_0.mp4", # no audio
        "gs://byron-alpha-vpagent/muxed_audio_output/muxed_output_1747264931.mp4",
    ]

    gcp_project = os.getenv('GOOGLE_CLOUD_PROJECT')
    print(f"Using Project ID: {gcp_project}") 
    print(f"Using Location: {test_location}")
    print(f"Input URIs: {test_input_uris}")

    if not gcp_project:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("Please ensure it's set in your .env file or your environment.")
        return

    # --- Calling the tool ---
    try:
        print(f"\nAttempting to join videos...")
        result_uri = await video_join_tool(
            location=test_location,
            input_uris=test_input_uris,
        )
        print(f"\nVideo join tool completed successfully!")
        print(f"Output GCS URI: {result_uri}")

    except ModuleNotFoundError as e:
        print(f"\nError: Could not import 'video_join_tool': {e}.")
        print(f"Please ensure 'video_join_tool.py' exists in the 'video_producer_agent' directory")
        print(f"and that the Python path is set up correctly. Current sys.path includes: {sys.path[0]}")
    except ValueError as ve:
        print(f"\nValueError during video join process: {ve}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the video join process: {type(e).__name__} - {e}")
        print("Ensure that GCS buckets exist, are accessible, and input URIs point to valid MP4 files.")
        print("Verify Transcoder API is enabled for your project and the location is correct.")
        # Consider re-raising the exception if this is part of an automated test suite
        # raise e

if __name__ == "__main__":
    # The load_dotenv() call is inside main() to ensure it's called when main() is executed.
    # Alternatively, it could be at the module level if preferred.
    asyncio.run(main())