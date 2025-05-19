import os
import trace
from dotenv import load_dotenv
from google.api_core.exceptions import GoogleAPICallError

# Assuming your updated text_to_speech function is in a file named text_to_speech_chirp.py
# If it's in the same file as the original, adjust the import accordingly.
from video_producer_agent.chirp_audio import text_to_speech # Import the wrapper function

load_dotenv()

def run_chirp_text_to_speech_example():
    """
    Runs a simple demonstration using the updated text_to_speech wrapper
    for Chirp 3 HD voices, synthesizing to GCS.
    """

    # --- Configuration ---
    load_dotenv()


    text_to_speak = (
        "This is a test sentence spoken by a Chirp 3 HD voice. "
        "It demonstrates the new text-to-speech functionality saving to a GCS bucket."
    )
    # --- End Configuration ---


    print(f"\n--- Synthesizing with Chirp 3 HD voice: 'chirp_female_aoede' (Plain Text) ---")

    gcs_uri_plain_text = text_to_speech(
        text=text_to_speak,
        voice_category="chirp_female_aoede",
        speaking_rate=1.0
    )




# --- Script Execution ---
if __name__ == "__main__":
    run_chirp_text_to_speech_example()