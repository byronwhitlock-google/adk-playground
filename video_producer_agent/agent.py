import random
import time
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from google.cloud import aiplatform
from google.adk.agents import LlmAgent
from google import genai
from google.genai import types
from vertexai.preview.generative_models import GenerativeModel
import vertexai
from video_generation_agent.agent import video_generation_agent, video_generation_tool


from typing import Sequence, Dict, Any


from video_producer_agent.tools import gcs_uri_to_public_url, generate_final_video_gcs_uri
from video_producer_agent.video_join_tool import video_join_tool



root_agent = Agent(
    name="video_producer_agent",
    model="gemini-2.0-flash",  #  Make sure this is the correct model identifier
    instruction="""
  You are an expert Commercial director, cinematographer and Producer AI Agent. Your primary function is to
  translate unstructured user thoughts and ideas for a TV commercial into a
  structured technical blueprint for production. You will analyze the user's
  creative brief and generate a detailed breakdown including scenes, narration, and punchy text overlays. 
  You will also generate a shot list for each scene, including camera angles, lighting, and other technical details.
  You will then pass this information to the video generation  to create the video clips.
  !IMPORTANT: only generate 2 scenes TOTAL.
   example video generation prompts:
      A video with smooth motion that dollies in on a desperate man in a green trench coat, using a vintage rotary phone against a wall bathed in an eerie green neon glow. The camera starts from a medium distance, slowly moving closer to the man's face, revealing his frantic expression and the sweat on his brow as he urgently dials the phone. The focus is on the man's hands, his fingers fumbling with the dial as he desperately tries to connect. The green neon light casts long shadows on the wall, adding to the tense atmosphere. The scene is framed to emphasize the isolation and desperation of the man, highlighting the stark contrast between the vibrant glow of the neon and the man's grim determination.

      Create a short 3D animated scene in a joyful cartoon style. A cute creature with snow leopard-like fur, large expressive eyes, and a friendly, rounded form happily prances through a whimsical winter forest. The scene should feature rounded, snow-covered trees, gentle falling snowflakes, and warm sunlight filtering through the branches. The creature's bouncy movements and wide smile should convey pure delight. Aim for an upbeat, heartwarming tone with bright, cheerful colors and playful animation.

      A satellite floating through outer space with the moon and some stars in the background.

      A POV shot from a vintage car driving in the rain, Canada at night, cinematic.
      
      A close-up of a girl holding adorable golden retriever puppy in the park, sunlight.
      
      Cinematic close-up shot of a sad woman riding a bus in the rain, cool blue tones, sad mood.
    
    -------
    Send the video generation  a scene by scene breakdown of each scene.
    The video generation  will then generate  video clips for each scene.
    
    Concatenate the generated clips together to create the final output video with a unique uri.
     create the uniue uri for the final output video using the generate_final_video_gcs_uri tool.
     pass the resulting uri to the video join tool to concatenate the video clips together.


    Convert the GCS URI of the video to a public URL and show the user inline in the browser.

   always pass gs://byron-alpha-vpagent bucket to the video generation .
   videos will be stored in this bucket

  """,
    tools=[
        #AgentTool(agent=video_generation_agent),
        gcs_uri_to_public_url,
        video_join_tool,
        video_generation_tool,
        
        
    ]
)
