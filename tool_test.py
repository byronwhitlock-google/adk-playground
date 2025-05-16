# tool_test.py

import asyncio
import os
import sys # Added to modify Python path
from datetime import datetime

from video_producer_agent.video_join_tool import video_join_tool




async def main():
    """
    Main function to test the video_join_tool.
    """
    # --- Configuration ---
    # These should be set in your .env file or environment.
    # If you use a .env file, ensure you have a library like python-dotenv to load it,
    # or that your execution environment (e.g., a shell script) loads it.
    # For example, with python-dotenv, you'd add:
    from dotenv import load_dotenv
    load_dotenv() # Load .env from project root

    # Get current datetime to include in the filename
    now = datetime.now()
    datetime_string = now.strftime("%Y%m%d_%H%M%S")

    # Example parameters for the video_join_tool
    test_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # Use from env or default

    # GCS URIs (as provided by you)
    test_input_uris = [
        "gs://byron-alpha-vpagent/muxed_audio_output/muxed_output_1747264766.mp4",
        #"gs://byron-alpha-vpagent/10717361122161337346/sample_0.mp4", # no audio
        "gs://byron-alpha-vpagent/muxed_audio_output/muxed_output_1747264931.mp4",
    ]

    print(f"Using Project ID: {os.getenv('GOOGLE_CLOUD_PROJECT')}") # Loaded from .env or environment
    print(f"Using Location: {test_location}")
    print(f"Input URIs: {test_input_uris}")

    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("Error: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("Please ensure it's set in your .env file (located at ./ .env) and loaded, or set in your environment.")
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

    except ModuleNotFoundError:
        print("\nError: Could not import 'video_join_tool'.")
        print(f"Please ensure 'video_join_tool.py' exists in '{video_agent_path}'")
        print(f"and that the Python path is set up correctly. Current sys.path includes: {sys.path[0]}")
    except ValueError as ve:
        print(f"\nValueError during video join process: {ve}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the video join process: {type(e).__name__} - {e}")
        print("Ensure that GCS buckets exist, are accessible, and input URIs point to valid MP4 files.")
        print("Verify Transcoder API is enabled for your project and the location is correct.")


if __name__ == "__main__":
    # To load .env automatically, you might use a library:
    # from dotenv import load_dotenv
    # load_dotenv() # This loads ./.env by default
    #
    # Then run the main async function
    asyncio.run(main())