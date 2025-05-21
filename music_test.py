from video_producer_agent.lyria_music import generate_lyria_music


print("Attempting to generate Lyria music (WAV) and upload to GCS...")

# Example 1: Generate two samples
print("\n--- Example 1: Upbeat Electronic (2 WAV samples) ---")
gcs_uris_1 = generate_lyria_music(
    prompt="Upbeat electronic dance music, 128 BPM, with a catchy synth melody and driving bassline.",
    negative_prompt="Piano"
)
if gcs_uris_1:
    print(f"Successfully generated and uploaded WAV music. GCS URIs: {gcs_uris_1}")
else:
    print("No WAV music was generated or uploaded in Example 1.")

# Example 2: Generate one sample using a seed
print("\n--- Example 2: Cinematic Ambient WAV with Seed ---")
gcs_uris_2 = generate_lyria_music(
    prompt="Cinematic ambient track, slow, atmospheric, with ethereal pads and a sense of wonder.",
    negative_prompt="drums, percussion, jarring sounds",
)
if gcs_uris_2:
    print(f"Successfully generated and uploaded WAV music. GCS URIs: {gcs_uris_2}")
else:
    print("No WAV music was generated or uploaded in Example 2.")
