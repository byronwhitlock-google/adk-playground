import asyncio
import os
import sys
from dotenv import load_dotenv
from video_producer_agent.mux_audio import mux_audio
from video_producer_agent.tools import gcs_uri_to_public_url

from google.protobuf.duration_pb2 import Duration # Relevant for understanding mux_audio's end_time_offset

# Load environment variables from .env file
load_dotenv()


async def run_mux_audio_test():
    """
    Executes the mux_audio function with hardcoded data for a real-world test.
    Ensures necessary environment variables are set and that the specified GCS URIs
    for video and audio files exist.
    """
    print("--- Starting Mux Audio Tool Real Execution Test ---")

    # --- Configuration ---
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") 

    # --- IMPORTANT: These GCS URIs must point to existing files for the test to pass ---
    test_video_uri = "gs://byron-alpha-vpagent/scene1.mp4/9575042869931285230/sample_0.mp4" # Video without audio or with audio to be replaced/mixed
    test_audio_uri = "gs://byron-alpha-vpagent/chirp_output_2061b46f-9c93-4f5a-9711-588e57951647.mp3" # Audio to be muxed
 
    # Note: The output bucket/path is defined within the mux_audio tool itself.

    # --- Pre-checks ---
    if not project_id:
        print("\nERROR: 'GOOGLE_CLOUD_PROJECT' environment variable is not set.")
        print("Please ensure it's defined in your .env file or your environment.")
        sys.exit(1) 

    print(f"Using Project ID: {project_id}")
    print(f"Using Location: {location}")
    print(f"Input Video URI: {test_video_uri}")
    print(f"Input Audio URI: {test_audio_uri}")

    # --- Execute the Tool ---
    try:
        print("\nCalling mux_audio...")
        final_output_uri = await mux_audio(
            video_uri=test_video_uri,
            audio_uri=test_audio_uri,
            end_time_offset=3.23, # Example: ensure audio is muxed for this duration
        )
        print("\n--- Mux Audio Tool Execution Completed Successfully! ---")
        print(f"Muxed output available at: {final_output_uri}")

        # Attempt to get and print the public URL
        try:
            public_url = gcs_uri_to_public_url(final_output_uri)
            print(f"Public URL: {public_url}")
        except Exception as url_e:
            print(f"Warning: Could not generate public URL for muxed output: {url_e}")

    except Exception as e:
        print(f"\n--- Mux Audio Tool Execution FAILED ---")
        print(f"An error occurred: {type(e).__name__} - {e}")
        print("\nPlease check the following:")
        print("  - Your Google Cloud project ID and location are correct.")
        print("  - The Transcoder API is enabled for your project.")
        print("  - The GCS input URIs are valid and accessible by the Transcoder service account.")
        print("  - The GCS output path (defined in mux_audio) is a valid bucket path and writable.")
        print("  - The input video (MP4) and audio files are in the expected formats.")
        # Consider re-raising the exception if this is part of an automated test suite that needs to catch failures
        # raise e 
        sys.exit(1) 

if __name__ == "__main__":
    asyncio.run(run_mux_audio_test())
