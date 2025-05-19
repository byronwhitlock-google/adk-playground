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


from video_producer_agent.mux_audio import get_linear16_audio_duration_gcs, mux_audio
from video_producer_agent.chirp_audio import  text_to_speech
from video_producer_agent.tools import gcs_uri_to_public_url
from video_producer_agent.video_join_tool import video_join_tool


# we cam add this into the prompt to padd the audio. otherwise, the video gets truncated 1 second afer the audio is done.
padding_prompt= 'If the audio is shorter than 8 seconds, regenerate with a longer <break time="0.5s"/> to pad silence at the end of the text to speech audio stream. To pad 1 second use <break time="1s"/> To pad 2 seconds use <break time="2s"/>.  the narration prompt should ALWAYS end with <break time="1s"/> tag to ensure the audio not cut off.  Pad dramatic pauses. To pad 1 second use <break time="1s"/> To pad 2 seconds use <break time="2s"/>'
prompt="""
  You are an expert Commercial director, cinematographer and Producer AI Agent. Your primary function is to
  translate unstructured user thoughts and ideas for a TV commercial into a
  structured technical blueprint for production. You will analyze the user's
  creative brief and generate a detailed scene by scene breakdown. 

    A good commercial effectively blends creativity, emotion, and storytelling with a clear representation of the brand's identity to capture the audience's attention and leave a lasting impression. It also includes a call to action and focuses on what the audience should do after seeing the commercial. 

  each scene should be 8 seconds long and include  the video generation prompt, the narration input for the text to speech tool, and the text overlays.
  
  Change up the voices and speed of speech for different scenes to keep it interesting.

  first use the narration to generate the audio stream for each scene using the text to speech tool. check the length with the get_linear16_audio_duration_gcs tool.


  if audio is longer than 10 seconds, first regenerate with a faster speaking rate up to 2.0. then try a shorter prompt. Only try 3 times before giving up.
  
  
  Mux each scenes audio stream and video stream together using the mux audio tool.
  The final commercial, join the video clips using the video join tool and convert the GCS URI of the video to a public URL.

  show a plan of the video generation and audio generation process, and ask the user for confirmation before starting.
  give a public URL to the video of each scene and the final video.

     example video generation prompts:
      A video with smooth motion that dollies in on a desperate man in a green trench coat, using a vintage rotary phone against a wall bathed in an eerie green neon glow. The camera starts from a medium distance, slowly moving closer to the man's face, revealing his frantic expression and the sweat on his brow as he urgently dials the phone. The focus is on the man's hands, his fingers fumbling with the dial as he desperately tries to connect. The green neon light casts long shadows on the wall, adding to the tense atmosphere. The scene is framed to emphasize the isolation and desperation of the man, highlighting the stark contrast between the vibrant glow of the neon and the man's grim determination.

      Create a short 3D animated scene in a joyful cartoon style. A cute creature with snow leopard-like fur, large expressive eyes, and a friendly, rounded form happily prances through a whimsical winter forest. The scene should feature rounded, snow-covered trees, gentle falling snowflakes, and warm sunlight filtering through the branches. The creature's bouncy movements and wide smile should convey pure delight. Aim for an upbeat, heartwarming tone with bright, cheerful colors and playful animation.

      A satellite floating through outer space with the moon and some stars in the background.

      A POV shot from a vintage car driving in the rain, Canada at night, cinematic.
      
      A close-up of a girl holding adorable golden retriever puppy in the park, sunlight.
      
      Cinematic close-up shot of a sad woman riding a bus in the rain, cool blue tones, sad mood.
    
    -------
    always use the gs://byron-alpha-vpagent bucket to the video generation .
    audio and videos will always be stored in this bucket
    generate the commercial one scene at a time.
  """
root_agent = Agent(
    name="video_producer_agent",
    model="gemini-2.0-flash",  #  Make sure this is the correct model identifier
    instruction=prompt,
    tools=[
        #AgentTool(agent=video_generation_agent),
        gcs_uri_to_public_url,
        video_join_tool,
        video_generation_tool,
        text_to_speech,
        mux_audio,
        get_linear16_audio_duration_gcs
        
    ]
)
