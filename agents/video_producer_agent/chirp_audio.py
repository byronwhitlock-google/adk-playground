import os
import uuid
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud.texttospeech_v1beta1.types import SsmlVoiceGender
from google.api_core.client_options import ClientOptions

# --- Voice Category Definitions for Chirp 3 HD Voices ---
VOICE_CATEGORY_DEFAULTS = {
    "chirp_female_aoede": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Aoede", "ssml_gender": SsmlVoiceGender.FEMALE, "description": "A high-definition female voice, offering improved clarity."},
    "chirp_male_puck": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Puck", "ssml_gender": SsmlVoiceGender.MALE, "description": "A high-definition male voice with clear articulation."},
    "chirp_male_charon": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Charon", "ssml_gender": SsmlVoiceGender.MALE, "description": "A high-definition male voice with a slightly deeper tone."},
    "chirp_female_kore": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Kore", "ssml_gender": SsmlVoiceGender.FEMALE, "description": "A high-definition female voice with a gentle quality."},
    "chirp_male_fenrir": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Fenrir", "ssml_gender": SsmlVoiceGender.MALE, "description": "A high-definition male voice suitable for authoritative narration."},
    "chirp_female_leda": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Leda", "ssml_gender": SsmlVoiceGender.FEMALE, "description": "A high-definition female voice with a smooth and flowing delivery."},
    "chirp_male_orus": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Orus", "ssml_gender": SsmlVoiceGender.MALE, "description": "A high-definition male voice with a commanding presence."},
    "chirp_female_zephyr": {"language_code": "en-US", "name": "en-US-Chirp3-HD-Zephyr", "ssml_gender": SsmlVoiceGender.FEMALE, "description": "A high-definition female voice with a bright and energetic tone."},
}


def text_to_speech(
    text: str,
    voice_category: str,
    speaking_rate: float = 1.0
) -> str:
    """
    Synthesizes plain text to mp3 audio using Chirp 3 HD voices and then uploads the generated
    audio file to a specified Google Cloud Storage bucket.

    This method performs real-time (online) synthesis, saves the audio locally,
    and then manually uploads to GCS. It is suitable for shorter audio outputs.
    SSML is NOT supported; the input 'text' must be plain text.

    Args:
        text: The plain text string to synthesize.
        voice_category: One of the defined Chirp 3 HD voice categories:
                        - `chirp_female_aoede`: A high-definition female voice, offering improved clarity.
                        - `chirp_male_puck`: A high-definition male voice with clear articulation.
                        - `chirp_male_charon`: A high-definition male voice with a slightly deeper tone.
                        - `chirp_female_kore`: A high-definition female voice with a gentle quality.
                        - `chirp_male_fenrir`: A high-definition male voice suitable for authoritative narration.
                        - `chirp_female_leda`: A high-definition female voice with a smooth and flowing delivery.
                        - `chirp_male_orus`: A high-definition male voice with a commanding presence.
                        - `chirp_female_zephyr`: A high-definition female voice with a bright and energetic tone.
        speaking_rate: Speed of speech (e.g., 1.0 for normal). Defaults to 1.0.

    Returns:
        The GCS URI (gs://bucket-name/file-name.wav) of the uploaded audio file.

    Raises:
        ValueError: If an invalid voice_category is provided or GOOGLE_CLOUD_PROJECT is not set.
        GoogleAPICallError: If the Text-to-Speech API call fails.
        Exception: For other unexpected errors during synthesis or upload.
    """
    pitch = 0.0
    volume_gain_db = 0.0
    timeout_seconds = 300.0

    gcs_bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "byron-alpha")
    google_cloud_location = "global" # Chirp 3 HD voices are available in 'global' for online synthesis

    

    if not google_cloud_project:
        google_cloud_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not google_cloud_project:
            raise ValueError("Google Cloud Project ID not provided and not found in environment variables.")

    normalized_category = voice_category.lower().replace(" ", "_")
    if normalized_category not in VOICE_CATEGORY_DEFAULTS:
        raise ValueError(
            f"Invalid voice_category: '{voice_category}'. "
            f"Valid options are: {', '.join(VOICE_CATEGORY_DEFAULTS.keys())}"
        )

    voice_config = VOICE_CATEGORY_DEFAULTS[normalized_category]

    # Initialize Text-to-Speech Client
    API_ENDPOINT = (
        f"{google_cloud_location}-texttospeech.googleapis.com"
        if google_cloud_location != "global"
        else "texttospeech.googleapis.com"
    )
    tts_client = texttospeech.TextToSpeechClient(
        client_options=ClientOptions(api_endpoint=API_ENDPOINT)
    )

    # Prepare input (always plain text as SSML is not supported)
    input_text = texttospeech.SynthesisInput(text=text)

    # Prepare voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_config["language_code"],
        name=voice_config["name"],
        ssml_gender=voice_config["ssml_gender"],
    )

    # Prepare audio config
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=pitch,
        volume_gain_db=volume_gain_db,
    )

    local_filename = f"chirp_output_{uuid.uuid4()}.mp3" 

    print(f"Synthesizing text with voice '{voice_category}' to local file '{local_filename}'...")
    try:
        # Perform the synthesis
        response = tts_client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config,
            timeout=timeout_seconds, # Apply timeout to the API call
        )

        # Save the audio content to a local file
        with open(local_filename, "wb") as out:
            out.write(response.audio_content)
        print(f"Audio content written to local file: '{local_filename}'")

        # Upload the local file to GCS
        storage_client = storage.Client(project=google_cloud_project)
        bucket = storage_client.bucket(gcs_bucket_name)
        blob = bucket.blob(local_filename)

        print(f"Uploading '{local_filename}' to GCS bucket '{gcs_bucket_name}'...")
        blob.upload_from_filename(local_filename)
        gcs_uri = f"gs://{gcs_bucket_name}/{local_filename}"
        print(f"✅ Audio successfully uploaded to GCS: {gcs_uri}")

        # Clean up local file (optional)
        os.remove(local_filename)
        print(f"Local file '{local_filename}' removed.")

        return gcs_uri

    except GoogleAPICallError as e:
        error_message = f"ERROR: Text-to-Speech API call failed: {e}"
        print(error_message)
        raise GoogleAPICallError(error_message) from e
    except Exception as e:
        error_message = f"ERROR: An unexpected error occurred during synthesis or upload: {e.__class__.__name__}: {e}"
        print(error_message)
        raise Exception(error_message) from e