import asyncio
import pprint
import time # Note: Your example used time.sleep, but the original script is async. Sticking to asyncio.sleep.
             # If this script is not run in an async context, time.sleep would be appropriate.

from google import genai
from google.genai import types

from dotenv import load_dotenv

import os
import uuid

async def image_and_text_to_video_tool(
    prompt: str,
    image_gcs_uri: str,
    image_mime_type: str, # e.g., "image/png", "image/jpeg"
    duration_seconds: int,
    
    ):
    """Tool to generate a video clip from an initial image and a text prompt using Veo.
    
    Args:
        prompt (str): The prompt to be sent to the video generation tool.
        image_gcs_uri (str): The GCS URI of the initial image.
        image_mime_type (str): The MIME type of the initial image (e.g., "image/png").
        duration_seconds (int): Desired duration of the generated video in seconds (e.g., 5-8 for Veo 2.0).
        aspect_ratio (str, optional): Desired aspect ratio (e.g., "16:9", "9:16"). Defaults to "16:9".
        
    Returns:
        types.GenerateVideosResponse: The response from the video generation tool, or string error.
    """
    try:
        load_dotenv()   
        bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "byron-alpha")
       # output_gcs_bucket = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")    
        aspect_ratio = "16:9" # Defaulting to 16:9 as in the example
    
        gcs_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")

        output_gcs_uri = f"gs://{gcs_bucket_name}/veo_image_to_video/{uuid.uuid4().hex}"


        # Initialize the client for the Generative AI API
        # Ensure GOOGLE_API_KEY is set in your environment or configured elsewhere for the client
        client = genai.Client()

        # Prepare the image input
        image_input = types.Image(
            gcs_uri=image_gcs_uri,
            mime_type=image_mime_type,
        )

        # Create the GenerateVideosConfig object
        generate_video_config = types.GenerateVideosConfig(
            duration_seconds=duration_seconds,
            number_of_videos=1,
            output_gcs_uri=output_gcs_uri, # This should be a GCS "directory" URI ending with /
            person_generation="allow_adult", # As in your original and example
            enhance_prompt=True, # From your original script, good to keep
            aspect_ratio=aspect_ratio # From the provided example
        )
        
        # Define the video model
        # Note: Ensure "veo-2.0-generate-001" or the appropriate model is available and supports image input.
        # The example used `video_model`, ensure this variable is set to the correct model string.
        # For clarity, I'm hardcoding it here as per your original script, but verify model capabilities.
       #  video_model_name = "veo-3.0-generate-preview"
        video_model_name = "veo-2.0-generate-001"


        print(f"Generating video with prompt: '{prompt}'")
        print(f"Initial image: {image_gcs_uri} ({image_mime_type})")
        print(f"Duration: {duration_seconds}s, Aspect Ratio: {aspect_ratio}")
        print(f"Output GCS URI: {output_gcs_uri}")


        # Create an operation to generate a video
        operation = client.models.generate_videos(
            model=video_model_name, # Use the specific model string
            prompt=prompt,
            image=image_input, # Add the image input here
            config=generate_video_config,
        )

        op=operation.name
        # The operation object itself has the .name attribute (if you need it for logging)
        print(f"Video generation operation started. Name: {op}")
        while not operation.done:
            await asyncio.sleep(5)
            operation = client.operations.get(operation)
            print("Waiting for video generation to complete...")
          

        print("Video generation operation finished.")
        print(operation)

        if operation.error:
            print(f"Video generation operation resulted in an error: {operation.error}")
            return f"Error: {operation.error}"
       
        return operation.result

        
    except Exception as e:
        # Catch any other general exceptions that might occur during the process
        return f"Error generating video: {str(e)}"
