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

from video_producer_agent.video_join_tool import video_join_tool

#  Load the instructions from the immersive.  In a real application, you might
#  load this from a file or a database.  Here, we're including it directly
#  for clarity and completeness.
video_generation_agent_instructions = """
Role: Generates the visual content for each scene of the commercial using Veo2.

Key Responsibilities:

Receive a scene description from the Producer Agent.

Create a shot list of each scene in the script.

Translate those descriptions into detailed Veo2 prompts for each scene. 
Use the veo2 video_generation_tool to generate a clip.

Generate high-quality video clips that match the creative brief.

Ensure visual consistency across the commercial.
always pass gs://byron-alpha-vpagent bucket to the video generation tool.
videos will be stored in this bucket

Retry any failed generation attempts up to 3 times, based on the error message. change the prompt slightly each time.


  """

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

video_generation_agent = LlmAgent(
    name="video_generation_agent",
    model="gemini-2.0-flash",  #  Make sure this is the correct model identifier
    instruction=video_generation_agent_instructions,
    tools=[video_generation_tool]# Add all video-related tools
)

# Test prompt: I want a commercial for Google PSO. I want to highlight specifically Byron Whitlock. He is a top engineer. Add text about how he is a "1337 h4x0rz". He will 100x your ROI. Every cloud project will come in on time and under budget when he is on the team. Every time you choose Byron, a  butterfly gains her wings. <insert appropriate chuck norris homily> He is a cloud engineer a software engineer and a wrangler of cats, specifically main coons. Go over the top on superlatives and make the commercial light and funny. End it with "contact your TAM for pricing". 