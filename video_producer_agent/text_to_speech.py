# Filename: text_to_speech_sync_explicit_args.py
# Description: A simplified, synchronous script for Google Text-to-Speech
#              synthesizing long audio directly to Google Cloud Storage.
#              Requires all synthesis parameters to be explicitly provided.

import uuid
from google.cloud import texttospeech_v1 as texttospeech
from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.cloud.texttospeech_v1.types import SsmlVoiceGender

# --- Voice Category Definitions ---
# (Same as before)
VOICE_CATEGORY_DEFAULTS = {
    "male_high": {"language_code": "en-US", "name": "en-US-Wavenet-D", "ssml_gender": SsmlVoiceGender.MALE},
    "female_high": {"language_code": "en-US", "name": "en-US-Wavenet-F", "ssml_gender": SsmlVoiceGender.FEMALE},
    "male_low": {"language_code": "en-US", "name": "en-US-Standard-D", "ssml_gender": SsmlVoiceGender.MALE},
    "female_low": {"language_code": "en-US", "name": "en-US-Standard-F", "ssml_gender": SsmlVoiceGender.FEMALE},
}
#TODO: FIgure out how to not hard code these values!!



#wrapper function
def text_to_speech(
    text: str,
    voice_category:str,
    speaking_rate:float
) -> str:
    """
    Synchronously synthesizes text to MP3 in GCS, requiring all params explicitly.

    Uses the synchronous Google Cloud Text-to-Speech client and handles long audio
    requests, blocking until the operation completes or times out.

    Args:
        text: SSML to synthesize. Must include <speak> tag. may include <voice> tags.        
        voice_category: one of male_high, female_high, male_low, female_low specifying the voice.
        speaking_rate: Speed of speech (e.g., 1.0 for normal).


    Returns:
    """
    return synthesize_text_to_gcs_sync(
        text=text,
        gcs_bucket_name="byron-alpha-vpagent",
        voice_category=voice_category,
        speaking_rate=speaking_rate,
        pitch=0.0,
        volume_gain_db=0.0,
        timeout_seconds=300.0,
        is_ssml=True,
        GOOGLE_CLOUD_PROJECT="byron-alpha", #TODO: parameterize
        GOOGLE_CLOUD_LOCATION="us-central1"
    )

# --- Core Synchronous Synthesis Function (NO Default Parameters) ---
def synthesize_text_to_gcs_sync(
    # Required parameters (no defaults):
    text: str,
    gcs_bucket_name: str,
    voice_category: str,
    speaking_rate: float,
    pitch: float,
    volume_gain_db: float,
    timeout_seconds: float,
    is_ssml: bool,
    GOOGLE_CLOUD_PROJECT: str,
    GOOGLE_CLOUD_LOCATION: str
) -> str:
    """
    (Synchronous) Synthesizes text to MP3 in GCS, requiring all params explicitly.

    Uses the synchronous Google Cloud Text-to-Speech client and handles long audio
    requests, blocking until the operation completes or times out.

    Args:
        text: The text (or SSML string) to synthesize.
        gcs_bucket_name: The name of the GCS bucket to store the output MP3.
        voice_category: One of male_high, female_high, male_low, female_low specifying the voice.
        speaking_rate: Speed of speech (e.g., 1.0 for normal).
        pitch: Pitch adjustment (e.g., 0.0 for normal).
        volume_gain_db: Volume gain adjustment (e.g., 0.0 for normal).
        timeout_seconds: Max seconds to wait for the synthesis operation to complete.
        is_ssml: True if 'text' contains SSML markup, False if plain text.

    Returns:
        The GCS URI (gs://bucket-name/file-name.pcm) of the synthesized audio file in LINEAR16 PCM format.

    Raises:
        ValueError: If an invalid voice_category is provided.
        GoogleAPICallError: If the API call or operation fails.
        TimeoutError: If waiting for the synthesis operation exceeds timeout_seconds.
        Exception: For other unexpected errors.
    """
    normalized_category = voice_category.lower().replace(" ", "_")
    if normalized_category not in VOICE_CATEGORY_DEFAULTS:
        raise ValueError(
            f"Invalid voice_category: '{voice_category}'. "
            f"Valid options are: {', '.join(VOICE_CATEGORY_DEFAULTS.keys())}"
        )

    voice_config = VOICE_CATEGORY_DEFAULTS[normalized_category]

    # 1. Use the SYNCHRONOUS client
    client = texttospeech.TextToSpeechLongAudioSynthesizeClient() 

    # 2. Prepare input, voice, and audio config
    if is_ssml:
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_config["language_code"],
        name=voice_config["name"],
        ssml_gender=voice_config["ssml_gender"],
    )

    # Use the explicitly passed parameters
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=speaking_rate,
        pitch=pitch,
        volume_gain_db=volume_gain_db,
        effects_profile_id=[],
    )

    # 3. Define output location and create request
    unique_filename = f"tts_output_{uuid.uuid4()}.pcm"
    gcs_output_uri = f"gs://{gcs_bucket_name}/{unique_filename}"

    request = texttospeech.SynthesizeLongAudioRequest(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
        output_gcs_uri=gcs_output_uri,
        parent=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}",
    )

    print(f"Starting synthesis operation for category '{voice_category}'. Output: {gcs_output_uri}")
    try:
        # 4. Initiate the long-running operation
        operation = client.synthesize_long_audio(request=request)

        print(f"Waiting for operation {operation.operation.name} to complete...")

        # 5. Wait for the operation to complete (using explicit timeout)
        result_metadata = operation.result(timeout=timeout_seconds)

        print(f"Synthesis successful! Audio saved to: {gcs_output_uri}")
        return gcs_output_uri

    except RetryError:
        error_message = f"ERROR: Synthesis operation timed out after {timeout_seconds} seconds for {gcs_output_uri}."
        print(error_message)
        raise TimeoutError(error_message)
    except GoogleAPICallError as e:
        error_message = f"ERROR: API call or operation failed for {gcs_output_uri}: {e}"
        print(error_message)
        raise GoogleAPICallError(error_message) from e
    except Exception as e:
        error_message = f"ERROR: An unexpected error occurred for {gcs_output_uri}: {e.__class__.__name__}: {e}"
        print(error_message)
        raise Exception(error_message) from e
