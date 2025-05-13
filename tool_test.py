# tool_test.py

import asyncio
import os
import sys # Added to modify Python path
from datetime import datetime

# Adjust the Python path to include the 'video_generation_agent' directory
# This allows us to import video_join_tool directly
# Assuming tool_test.py is in the project root and video_join_tool.py is in ./video_generation_agent/
project_root = os.path.dirname(os.path.abspath(__file__))
video_agent_path = os.path.join(project_root, "video_generation_agent")
if video_agent_path not in sys.path:
    sys.path.insert(0, video_agent_path)

from video_producer_agent.video_join_tool import video_join_tool
from dotenv import load_dotenv

load_dotenv()

async def main():
    """
    Main function to test the video_join_tool.
    """
    print("Starting video_join_tool test harness...")
    print(f"Attempting to import 'video_join_tool' from: {video_agent_path}")


    # --- Configuration ---
    # These should be set in your .env file or environment.
    # If you use a .env file, ensure you have a library like python-dotenv to load it,
    # or that your execution environment (e.g., a shell script) loads it.
    # For example, with python-dotenv, you'd add:
    # from dotenv import load_dotenv
    # load_dotenv(os.path.join(project_root, ".env")) # Load .env from project root

    # Get current datetime to include in the filename
    now = datetime.now()
    datetime_string = now.strftime("%Y%m%d_%H%M%S")

    # Example parameters for the video_join_tool
    test_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # Use from env or default

    # GCS URIs (as provided by you)
    test_input_uris = [
        "gs://byron-alpha-vpagent/butterfly.mp4/682121198586463595/sample_0.mp4",
        "gs://byron-alpha-vpagent/12786537024005683176/sample_0.mp4",
        "gs://byron-alpha-vpagent/15139875958009000989/sample_0.mp4",
    ]
    # IMPORTANT: Replace 'your-output-bucket-name' with your actual output bucket GCS URI
    test_output_uri_prefix = "gs://byron-alpha-vpagent/TESTjoined_videos_output/"
    test_output_filename = f"joined_video_{datetime_string}.mp4"

    print(f"Using Project ID: {os.getenv('GOOGLE_CLOUD_PROJECT')}") # Loaded from .env or environment
    print(f"Using Location: {test_location}")
    print(f"Input URIs: {test_input_uris}")
    print(f"Output URI Prefix: {test_output_uri_prefix}")
    print(f"Output Filename: {test_output_filename}")

    # --- Pre-checks (Optional but Recommended) ---
    if "your-output-bucket-name" in test_output_uri_prefix:
        print("\nWARNING: Placeholder GCS output URI prefix is being used.")
        print(f"Please replace 'your-output-bucket-name' in '{test_output_uri_prefix}' with an actual GCS bucket name.")
        print("The tool will likely fail if this is not an actual accessible GCS path.\n")
        # return # You might want to exit if placeholders are detected

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
            output_uri_prefix=test_output_uri_prefix,
            output_filename=test_output_filename
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