import asyncio
import os
import pprint
from dotenv import load_dotenv
from google.api_core.exceptions import GoogleAPICallError

# Import the video_generation_tool function
from video_producer_agent.video_generation_tool import video_generation_tool

load_dotenv()

async def run_video_generation_example():
    """
    Runs a simple demonstration using the video_generation_tool.
    """
    print("\n--- Starting Video Generation Tool Example ---")

    # --- Configuration for video generation ---
    # These parameters are examples. Adjust them as needed for your tests.
    test_prompt = "A futuristic city at sunset with flying cars and towering skyscrapers."
    test_aspect_ratio = "16:9"
    test_duration_seconds = 5  # Max 8 seconds
    test_enhance_prompt = True
    test_negative_prompt = "blurry, low resolution, ugly, deformed"
    test_number_of_videos = 1 # This parameter is not used in the tool's current signature
    test_person_generation = "dont_allow" # or "allow_adult"
    test_seed = 12345

    print(f"Attempting to generate video with prompt: '{test_prompt}'")
    print(f"Aspect Ratio: {test_aspect_ratio}, Duration: {test_duration_seconds}s")

   
    # Call the video_generation_tool with the defined parameters
    result = await video_generation_tool(
        prompt=test_prompt,
        aspect_ratio=test_aspect_ratio,
        duration_seconds=test_duration_seconds,
        enhance_prompt=test_enhance_prompt,
        negative_prompt=test_negative_prompt,
        person_generation=test_person_generation,
        seed=test_seed
    )

    # Print the result of the video generation
    if isinstance(result, str) and "Error:" in result:
        print(f"\nVideo Generation Failed: {result}")
        pprint.pprint(result)
    elif isinstance(result, str) and result.startswith("gs://"): # Check if it's a GCS URI string
        print("\nVideo Generation Succeeded!")
        print("Generated Video Details:")
        print(f"  GCS URI: {result}") # Directly print the GCS URI
        print("-" * 20)
    else:
        # This else block would catch unexpected successful return types
        print(f"\nVideo Generation Succeeded with unexpected result type: {type(result)}")
        pprint.pprint(result)


    print("\n--- Video Generation Tool Example Finished ---")

# --- Script Execution ---
if __name__ == "__main__":
    # Run the asynchronous test function
    asyncio.run(run_video_generation_example())