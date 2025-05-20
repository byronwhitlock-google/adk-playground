from google.adk.agents import LlmAgent
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.cloud import aiplatform
from google.adk.agents import LlmAgent

from google import genai
from google.genai import types

from vertexai.preview.generative_models import GenerativeModel
import vertexai

import random
import time

from typing import Sequence, Dict, Any


import uuid
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.services.transcoder_service import (
    TranscoderServiceClient,
)
from google.api_core import exceptions as google_api_exceptions

async def video_generation_tool(
    prompt: str,
    generateVideoConfig: types.GenerateVideosConfig,
    tool_context: ToolContext
    ):
    """Tool to generate an 8 second video clip from an description using Veo2.
    
    Args:
        prompt (str): The prompt to be sent to the video generation tool
        generateVideoConfig (types.GenerateVideosConfig): The configuration for the video generation tool.
        tool_context (ToolContext): The tool context for storing artifacts
    Returns:
        types.GenerateVideosResponse: The response from the video generation tool. 
    """
    try:
        # Initialize the client for the Generative AI API
        client = genai.Client()

        # Create an operation to generate a video
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt,
            config=generateVideoConfig,
        )

        # Wait for video generation to complete
        while not operation.done:
            time.sleep(20)
            operation = client.operations.get(operation)

        
        return operation.response.generated_videos
        
    except Exception as e:
        return f"Error generating video: {str(e)}"
