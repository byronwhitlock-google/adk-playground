
# This script tests synchronous text-to-speech synthesis to GCS,
# specifically using the `synthesize_text_to_gcs_sync` function
# which requires all synthesis parameters to be explicitly provided.

from video_producer_agent.text_to_speech import synthesize_text_to_gcs_sync
from google.api_core.exceptions import GoogleAPICallError
from dotenv import load_dotenv

load_dotenv()

def run_sync_explicit_example():
    """
    Runs a simple demonstration of `synthesize_text_to_gcs_sync`
    requiring explicit arguments for synthesis.
    """

    # --- Configuration ---
    gcs_bucket_name = "byron-alpha-vpagent" # Target GCS bucket for output
    google_cloud_project = "byron-alpha"     # GCP Project ID for the API call
    google_cloud_location = "us-central1"    # GCP Location for the API call

    text_to_speak = (
        "This test requires explicit parameters for speaking rate, pitch, "
        "volume, timeout, and SSML flag."
    )
    # --- End Configuration ---

    print(f"\n--- Synthesizing with category: 'male_low' (Plain Text - Explicit Args) ---")
    try:
        # Call the synchronous function providing ALL required arguments explicitly
        # Note: effects_profile_id is handled internally by synthesize_text_to_gcs_sync
        gcs_uri = synthesize_text_to_gcs_sync(
            text=text_to_speak,
            gcs_bucket_name=gcs_bucket_name,
            voice_category="male_low",
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0,
            timeout_seconds=300.0,
            is_ssml=False, 
            GOOGLE_CLOUD_PROJECT=google_cloud_project,
            GOOGLE_CLOUD_LOCATION=google_cloud_location,
        )
        print(f"✅ Plain text synthesis complete for 'male_low'. File at: {gcs_uri}")

    except (ValueError, GoogleAPICallError, TimeoutError, Exception) as e:
        print(f"❌ Failed for category 'male_low': {e}")

# --- Script Execution ---
if __name__ == "__main__":
    run_sync_explicit_example()
