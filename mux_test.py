import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from video_producer_agent.mux_audio import mux_audio
from video_producer_agent.tools import gcs_uri_to_public_url

from google.protobuf.duration_pb2 import Duration # Import Duration type for time offsets

# Load environment variables from .env file
load_dotenv()


async def run_mux_audio_test():
    """
    Executes the mux_audio function with hardcoded data for a real-world test.
    Ensures necessary environment variables are set.
    """
    print("--- Starting Mux Audio Tool Real Execution Test ---")

    # --- Configuration ---
    # Retrieve configuration from environment variables (set in .env or your shell)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # Default to us-central1 if not set

    # --- IMPORTANT: Replace with your actual GCS URIs for testing ---
    # Ensure these video and audio files exist in your GCS bucket
    test_video_uri = "gs://byron-alpha-vpagent/scene1.mp4/9575042869931285230/sample_0.mp4"
    test_audio_uri = "gs://byron-alpha-vpagent/tts_output_e2e663f6-5a76-4cf3-848e-aebde41462ee.pcm"
 
    # Ensure this output bucket exists and is writable by your Transcoder service account
    test_output_uri_base = "gs://byron-alpha-vpagent/muxed_audio_output/" 

    # --- Pre-checks ---
    if not project_id:
        print("\nERROR: 'GOOGLE_CLOUD_PROJECT' environment variable is not set.")
        print("Please ensure it's defined in your .env file or your environment.")
        sys.exit(1) # Exit if project ID is missing

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
            end_time_offset=2,
            location=location,
        )
        print("\n--- Mux Audio Tool Execution Completed Successfully! ---")
        #print(final_output_uri)
        print(f"Muxed output available at: {final_output_uri}")

    except Exception as e:
        print(f"\n--- Mux Audio Tool Execution FAILED ---")
        print(f"An error occurred: {type(e).__name__} - {e}")
        print("\nPlease check the following:")
        print("  - Your Google Cloud project ID and location are correct.")
        print("  - The Transcoder API is enabled for your project.")
        print("  - The GCS input URIs are valid and accessible by the Transcoder service account.")
        print("  - The GCS output URI base is a valid bucket path and writable.")
        print("  - The input video (MP4) and audio (e.g., LINEAR16 PCM) files are in the expected formats.")
        sys.exit(1) # Exit with an error code on failure

if __name__ == "__main__":
    asyncio.run(run_mux_audio_test())
