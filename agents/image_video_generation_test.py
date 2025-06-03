import asyncio
import os
import pprint
from dotenv import load_dotenv

# Assuming image_video_generation_tool.py is in the same directory
# or accessible via PYTHONPATH.
# If it's in a package, adjust the import accordingly.
# e.g., from my_package.image_video_generation_tool import image_and_text_to_video_tool
try:
    from video_producer_agent.image_video_generation_tool import image_and_text_to_video_tool
    from video_producer_agent.tools import gcs_uri_to_public_url
except ImportError:
    print("Error: Could not import image_and_text_to_video_tool.")
    print("Ensure image_video_generation_tool.py is in the same directory or in PYTHONPATH.")
    # As a fallback, if you have a specific package structure like the example, you might use:
    # from video_producer_agent.image_video_generation_tool import image_and_text_to_video_tool
    exit(1)


async def run_image_to_video_generation_example():
    """
    Runs a demonstration using the image_and_text_to_video_tool.
    """
    print("\n--- Starting Image-to-Video Generation Tool Example ---")

    # --- Configuration for image-to-video generation ---
    # These parameters are examples. Adjust them as needed for your tests.
    test_prompt = "Raising arms in glory"
    test_image_gcs_uri = "gs://byron-alpha-vpagent/1575485587611.jpeg" # Provided by user
    test_image_mime_type = "image/jpeg" # Inferred from the .jpeg extension
    test_duration_seconds = 6  # Example duration, Veo 2.0 typically supports 5-8 seconds

    print(f"Attempting to generate video with prompt: '{test_prompt}'")
    print(f"Initial Image GCS URI: {test_image_gcs_uri}")
    print(f"Image MIME Type: {test_image_mime_type}")
    print(f"Target Duration: {test_duration_seconds}s")

    # Call the image_and_text_to_video_tool with the defined parameters
    # The tool itself handles aspect_ratio and other configurations internally or via env vars

    result = await image_and_text_to_video_tool(
        prompt=test_prompt,
        image_gcs_uri=test_image_gcs_uri,
        image_mime_type=test_image_mime_type,
        duration_seconds=test_duration_seconds
    )

    print("\n--- Raw Result from Tool ---")
    pprint.pprint(result, indent=2)

    if isinstance(result, str) and result.startswith("Error"):
        print(f"\nTool returned an error: {result}")
    elif hasattr(result, 'generated_videos') and result.generated_videos:
        print("\n--- Video Generation Successful ---")
        for i, video_info in enumerate(result.generated_videos):
            print(f"  Video {i+1} URI: {gcs_uri_to_public_url(video_info.video.uri)}")
            
    elif hasattr(result, 'operation') and result.operation.error:
            print(f"\nVideo generation operation resulted in an error: {result.operation.error.message}")
    elif result:
        print("\nTool returned a response, but structure might be unexpected. Please review raw output.")
    else:
        print("\nTool did not return a recognizable success or error message.")



# --- Script Execution ---
if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    # The image_video_generation_tool.py also does this, but it's good practice
    # for the test script to ensure the environment is set up before calling the tool.
    load_dotenv()
    
    # Ensure necessary environment variables are set (as an example check)
    # The actual tool will handle more specific checks or defaults.
    required_env_vars = ["GOOGLE_API_KEY", "GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_BUCKET"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Warning: The following environment variables are not set: {', '.join(missing_vars)}")
        print("The tool might fail or use defaults if these are required.")

    # Run the asynchronous test function
    asyncio.run(run_image_to_video_generation_example())
