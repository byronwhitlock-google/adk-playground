import os
from dotenv import load_dotenv
from video_producer_agent.mux_audio import get_mp3_audio_duration_gcs
from video_producer_agent.chirp_audio import text_to_speech
from video_producer_agent.tools import gcs_uri_to_public_url

# Load environment variables from .env file
load_dotenv()

def run_chirp_text_to_speech_example():
    """
    Runs a simple demonstration using the text_to_speech wrapper
    for Chirp 3 HD voices, synthesizing to GCS, then prints its duration and public URL.
    """

    # --- Configuration ---
    text_to_speak = (
        "This is a test sentence spoken by a Chirp 3 HD voice....It"
        " demonstrates the new text-to-speech functionality saving to a GCS"
        " bucket."
    )
    # --- End Configuration ---


    print(f"\n--- Synthesizing with Chirp 3 HD voice: 'chirp_female_aoede' (Plain Text) ---")

    gcs_uri_plain_text = text_to_speech(
        text=text_to_speak,
        voice_category="chirp_female_aoede",
        speaking_rate=1.0
    )

    print ("Audio GCS URI: ", gcs_uri_plain_text)

    # Get and print the duration of the synthesized audio
    duration = get_mp3_audio_duration_gcs(gcs_uri_plain_text)
    print ("Audio duration (seconds): ", duration)

    # Get and print the public URL of the synthesized audio
    public_url = gcs_uri_to_public_url(gcs_uri_plain_text)
    print("Public URL: ", public_url)






# --- Script Execution ---
if __name__ == "__main__":
    run_chirp_text_to_speech_example()