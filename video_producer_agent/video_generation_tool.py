import pprint
from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.cloud import aiplatform
from google.adk.agents import LlmAgent

from google import genai
from google.genai import types

from vertexai.preview.generative_models import GenerativeModel
import vertexai
from dotenv import load_dotenv

import random
import time
import os
from typing import Sequence, Dict, Any


import uuid
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.services.transcoder_service import (
    TranscoderServiceClient,
)
from google.api_core import exceptions as google_api_exceptions

async def video_generation_tool(
    prompt: str,
    duration_seconds: int 
    ):
    """Tool to generate an 8 second video clip from an description using Veo2.
    
    Args:
        prompt (str): The prompt to be sent to the video generation tool
        duration_seconds (int): Desired duration of the generated video in seconds valid values are (5,6,7,8).
    Returns:
        types.GenerateVideosResponse: The response from the video generation tool.
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
        )

        # Create an operation to generate a video
        operation =  client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt,
            config=generate_video_config,
        )
        # Wait for video generation to complete
        while not operation.done:
            time.sleep(2)
            operation = client.operations.get(operation)
        pprint.pprint(operation)
        
        return operation.response
        
        
        # # Explicitly check the type of operation immediately after the call
        # if not isinstance(operation, types.GenerateVideosOperation): # Assuming genai.Client returns types.Operation
        #     return f"Error: Expected an operation object, but received: {type(operation).__name__} - {operation}"

        # # Wait for video generation to complete
        # while operation.done == None:
        #     time.sleep(1) # Still sleep to wait for completion
        #     if not hasattr(operation, 'name'):
        #         return f"Error: Operation object missing 'name' attribute during status check. Type: {type(operation).__name__}"
        #     pprint.pprint (operation)
        #    # print ("tring this op "+op.name)
        #     operation =   client.operations.get(operation.name) # Use operation.name to get the latest status

        # # Check if the operation completed successfully and has a response
        # if operation.done :
        #     if operation.error:
        #         # If there's an error in the operation, return the error message
        #         return f"Video generation failed with error: {operation.error.message} (Code: {operation.error.code})"
        #     elif operation.response:
        #         # Check if 'generated_videos' attribute exists before accessing it
        #         if hasattr(operation.response, 'generated_videos'):
        #             return operation.response.generated_videos
        #         else:
        #             # If 'generated_videos' is not found, it means the response structure is unexpected
        #             return "Error: 'generated_videos' attribute not found in the operation response."
        #     else:
        #         # If operation.response is None, but no error, indicate no response
        #         return "Error: Video generation operation completed but returned no response."
        # else:
        #     # This case should ideally not be hit if the while loop exits because operation.done is true
        #     return "Error: Video generation operation did not complete successfully."

    except Exception as e:
        # Catch any other general exceptions that might occur during the process
        #return f"Error generating video: {str(e)}"
        raise e