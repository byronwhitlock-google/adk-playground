import asyncio
import pprint

from google import genai
from google.genai import types

from dotenv import load_dotenv

import os


import uuid

async def video_generation_tool(
    prompt: str,
    duration_seconds: int 
    ):
    """Tool to generate an 8 second video clip from an description using Veo2.
    
    Args:
        prompt (str): The prompt to be sent to the video generation tool
        duration_seconds (int): Desired duration of the generated video in seconds valid values are (5,6,7,8).
    Returns:
        types.GenerateVideosResponse: The response from the video generation tool. or string error
    """
    try:

        load_dotenv()   

        gcs_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")

        output_gcs_uri=f"gs://{gcs_bucket_name}/veo2/"+ uuid.uuid4().hex


        # Initialize the client for the Generative AI API
        client = genai.Client()

        # Create the GenerateVideosConfig object
        generate_video_config = types.GenerateVideosConfig(
            duration_seconds=duration_seconds,
            number_of_videos=1,
            output_gcs_uri=output_gcs_uri,
            person_generation="allow_adult",
            enhance_prompt=True,
        )

        # Create an operation to generate a video
        operation =  client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt,
            config=generate_video_config,
        )
        # Wait for video generation to complete
        while not operation.done:
            await asyncio.sleep(5) # Polling interval (e.g., 15 seconds)
            operation = client.operations.get(operation)
        pprint.pprint(operation)
        
        return operation.response
        
        
    except Exception as e:
        # Catch any other general exceptions that might occur during the process
        return f"Error generating video: {str(e)}"
        #raise e