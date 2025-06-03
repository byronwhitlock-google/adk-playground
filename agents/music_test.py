"""
This script tests the Lyria music generation functionality.

It calls the `generate_lyria_music` tool from the `video_producer_agent`
with different prompts to generate music samples and verifies their upload to GCS.
"""
from video_producer_agent.lyria_music import generate_lyria_music


print("Attempting to generate Lyria music (WAV) and upload to GCS...")

# Example 1: Generate one upbeat electronic sample
print("\n--- Example 1: Upbeat Electronic (1 WAV sample) ---")
gcs_uri_1 = generate_lyria_music(
    prompt="Upbeat electronic dance music, 128 BPM, with a catchy synth melody and driving bassline.",
    negative_prompt="Piano"
)
if gcs_uri_1 and not gcs_uri_1.startswith("ERROR:"):
    print(f"Successfully generated and uploaded WAV music. GCS URI: {gcs_uri_1}")
else:
    print(f"Music generation or upload failed for Example 1. Result: {gcs_uri_1}")

# Example 2: Generate one cinematic ambient sample
print("\n--- Example 2: Cinematic Ambient WAV ---")
gcs_uri_2 = generate_lyria_music(
    prompt="Cinematic ambient track, slow, atmospheric, with ethereal pads and a sense of wonder.",
    negative_prompt="drums, percussion, jarring sounds",
)
if gcs_uri_2 and not gcs_uri_2.startswith("ERROR:"):
    print(f"Successfully generated and uploaded WAV music. GCS URI: {gcs_uri_2}")
else:
    print(f"Music generation or upload failed for Example 2. Result: {gcs_uri_2}")
