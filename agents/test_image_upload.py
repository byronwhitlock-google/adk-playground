
# --- Example of how to call the function (for demonstration) ---
# To use this:
# 1. Ensure google-cloud-storage and google-auth are installed:
#    pip install google-cloud-storage google-auth
# 2. Set environment variables:
#    export GOOGLE_CLOUD_BUCKET="your-gcs-bucket-name"
#    export GOOGLE_CLOUD_PROJECT="your-gcp-project-id" # Optional, but recommended
# 3. Make sure you are authenticated with GCP (e.g., run `gcloud auth application-default login`)
# 4. Create a dummy image file, e.g., "my_test_image.png"

import os

from video_producer_agent.upload_image import store_image_artifact_in_gcs
from dotenv import load_dotenv

load_dotenv()


print("Demonstrating GCS Image Upload Function (ensure environment is set up)")

# Create a dummy PNG file for the demonstration
dummy_image_file = "temp_example_image.png"
dummy_text_file = "temp_example_text.txt"

try:
    with open(dummy_image_file, "wb") as f:
        # Minimal valid PNG (1x1 white pixel)
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53\xDE\x00\x00\x00\x01sRGB\x00\xAE\xCE\x1C\xE9\x00\x00\x00\x0CIDAT\x08\xD7c\xF8\xFF\xFF\xFF\x00\x00\x00\x00IEND\xAEB`\x82')
    print(f"Created dummy image: {dummy_image_file}")

    with open(dummy_text_file, "w") as f:
        f.write("This is a test text file, not an image.")
    print(f"Created dummy text file: {dummy_text_file}")


    # Check if GOOGLE_CLOUD_BUCKET is set, otherwise skip the call
    if not os.getenv("GOOGLE_CLOUD_BUCKET"):
        print("\nSKIPPING UPLOAD DEMO: GOOGLE_CLOUD_BUCKET environment variable is not set.")
        print("Please set it to your GCS bucket name to test the upload.")
    else:
        print(f"\n--- Test 1: Uploading valid image ({dummy_image_file}) ---")
        print(f"Attempting upload to bucket: {os.getenv('GOOGLE_CLOUD_BUCKET')}")
        result1 = store_image_artifact_in_gcs(dummy_image_file, gcs_destination_blob_prefix="test_uploads/")
        if result1.startswith("gs://"):
            print(f"Demo Success: Uploaded image GCS URI: {result1}")
        else: # It's an error string
            print(f"Demo Failure: {result1}")

        print(f"\n--- Test 2: Attempting to upload non-image file ({dummy_text_file}) ---")
        result2 = store_image_artifact_in_gcs(dummy_text_file, gcs_destination_blob_prefix="test_uploads/")
        if result2.startswith("gs://"):
            print(f"Demo Unexpected Success (should have failed): {result2}")
        else:
            print(f"Demo Expected Failure: {result2}")
        
        print(f"\n--- Test 3: Attempting to upload non-existent file ---")
        result3 = store_image_artifact_in_gcs("non_existent_file.png", gcs_destination_blob_prefix="test_uploads/")
        if result3.startswith("gs://"):
            print(f"Demo Unexpected Success (should have failed): {result3}")
        else:
            print(f"Demo Expected Failure: {result3}")


except Exception as e:
    print(f"Error in demonstration: {e}")
finally:
    if os.path.exists(dummy_image_file):
        os.remove(dummy_image_file)
        print(f"Cleaned up dummy image: {dummy_image_file}")
    if os.path.exists(dummy_text_file):
        os.remove(dummy_text_file)
        print(f"Cleaned up dummy text file: {dummy_text_file}")

