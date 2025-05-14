
# --- Synchronous Example Usage (Explicit Arguments) ---
from video_producer_agent.text_to_speech import synthesize_text_to_gcs_sync

from google.api_core.exceptions import GoogleAPICallError # <-- Add this import
from dotenv import load_dotenv

load_dotenv()
def run_sync_explicit_example():
    """Runs a simple demonstration requiring explicit args for synthesis."""

    # --- Configuration ---
    your_gcs_bucket = "byron-alpha-vpagent"

    text_to_speak = (
        "This test requires explicit parameters for speaking rate, pitch, "
        "volume, effects, timeout, and SSML flag."
    )
    # --- End Configuration ---

    if your_gcs_bucket == "your-gcs-bucket-name-here" or not your_gcs_bucket:
        print("🔴 CRITICAL: Please open this script and replace "
              "'your-gcs-bucket-name-here' with your actual GCS bucket name.")
        return

    print(f"\n--- Synthesizing with category: 'male_low' (Plain Text - Explicit Args) ---")
    try:
        # Call the synchronous function providing ALL arguments explicitly
        gcs_uri = synthesize_text_to_gcs_sync(
            text=text_to_speak,
            gcs_bucket_name=your_gcs_bucket,
            voice_category="male_low",
            # --- Provide values for previously defaulted arguments ---
            speaking_rate=1.0,      # Provide rate (1.0 = normal)
            pitch=0.0,              # Provide pitch (0.0 = normal)
            volume_gain_db=0.0,     # Provide volume (0.0 = normal)
            effects_profile_id=None,# Provide effects profile (None = none)
            timeout_seconds=300.0,  # Provide timeout
            is_ssml=False,           # Provide SSML flag
            GOOGLE_CLOUD_PROJECT="byron-alpha", # Replace with your project ID
            GOOGLE_CLOUD_LOCATION="us-central1", # Replace with your location
            # --- End explicit arguments ---
        )
        print(f"✅ Plain text synthesis complete for 'male_low'. File at: {gcs_uri}")

    except (ValueError, GoogleAPICallError, TimeoutError, Exception) as e:
        print(f"❌ Failed for category 'male_low': {e}")

# --- Script Execution ---
if __name__ == "__main__":


    run_sync_explicit_example() # Call the example function
