import asyncio
import os
import sys
from dotenv import load_dotenv
# This test uses video_producer_agent.mux_music to combine a video with background music.

from video_producer_agent.mux_audio import get_mp3_audio_duration_gcs
from video_producer_agent.mux_music import mux_music
from video_producer_agent.tools import gcs_uri_to_public_url

from google.cloud.video import transcoder_v1 # Transcoder API client, used by mux_music
from video_producer_agent.video_length_tool import get_video_length_gcs_partial_download # For getting video duration

# Load environment variables from .env file
load_dotenv()

async def run_mux_music_test():
    """
    Executes the mux_music function with hardcoded data for a real-world test.
    Ensures necessary environment variables are set and that the specified GCS
    URIs for video and music files exist.
    """
    print("--- Starting Mux Music Tool Real Execution Test ---")

    # --- Configuration ---
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    # --- IMPORTANT: These GCS URIs must point to existing files for the test to pass ---
    test_video_with_audio_uri = "gs://byron-alpha-vpagent/muxed/f5b390610a2a4fb9bc83808e876b5e7e.mp4" # MP4 with existing audio/video
    test_music_uri = "gs://byron-alpha-vpagent/lyria_output_7d7be0d3-8ef4-4044-8641-55d61a7dc953.wav"    # WAV music file

    test_volume_music = 0.3 # Volume for the background music (0.0 to 1.0)

    # Note: The output base URI is defined within the mux_music tool itself.
    # test_output_uri_base = "gs://byron-alpha-vpagent/muxed_music_output/" 

    # --- Pre-checks ---
    if not project_id:
        print("\nERROR: 'GOOGLE_CLOUD_PROJECT' environment variable is not set.")
        print("Please ensure it's defined in your .env file or your environment.")
        sys.exit(1)
    
    print("Fetching video and music durations...")
    video_duration = get_video_length_gcs_partial_download(test_video_with_audio_uri)
    if isinstance(video_duration, str) and video_duration.startswith("Error"):
        print(f"Failed to get video duration: {video_duration}")
        sys.exit(1)
        
    music_duration = get_mp3_audio_duration_gcs(test_music_uri)
    if isinstance(music_duration, str) and music_duration.startswith("Error"):
        print(f"Failed to get music duration: {music_duration}")
        sys.exit(1)

    print(f"Using Project ID: {project_id}")
    print(f"Using Location: {location}")
    print(f"Input MP4 with Audio/Video URI: {test_video_with_audio_uri}")
    print(f"Input Music (WAV) URI: {test_music_uri}")
    print(f"Music Volume: {test_volume_music}")
    print(f"Main Video Duration (seconds): {video_duration}")
    print(f"Music Duration (seconds): {music_duration}")





    # --- Execute the Tool ---
    try:
        print("\nCalling mux_music...")
        final_output_uri = await mux_music(
            video_with_audio_uri=test_video_with_audio_uri,
            music_uri=test_music_uri,
            main_video_duration=video_duration, # Pass the duration as a parameter
            music_duration=music_duration,
            volume_music=test_volume_music,
        )
        print("\n--- Mux Music Tool Execution Completed Successfully! ---")
        print(f"Muxed output with background music available at: {final_output_uri}")

        try:

            print(f"Original URL: {gcs_uri_to_public_url(test_video_with_audio_uri)}")
        
            public_url = gcs_uri_to_public_url(final_output_uri)
            print(f"Public URL: {public_url}")
        except Exception as url_e:
            print(f"Warning: Could not generate public URL: {url_e}")

    except Exception as e:
        print(f"\n--- Mux Music Tool Execution FAILED ---")
        print(f"An error occurred: {type(e).__name__} - {e}")
        print("\nPlease check the following:")
        print("  - Your Google Cloud project ID and location are correct.")
        print("  - The Transcoder API is enabled for your project.")
        print("  - The GCS input URIs are valid and accessible by the Transcoder service account.")
        print("  - The GCS output bucket (derived from hardcoded base in mux_music) is valid and writable.")
        print("  - The input MP4 and WAV files are in the expected formats.")
        raise e

if __name__ == "__main__":
    asyncio.run(run_mux_music_test())