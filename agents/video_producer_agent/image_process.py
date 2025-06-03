import google.genai.types as types
from google.cloud import storage
from google.api_core import exceptions
import tempfile
import os
import uuid

from .upload_image import store_image_artifact_in_gcs
import os
from adk.api.tool_next import tool
from adk.api.tool_next import ToolInput

@tool
def save_uploaded_image(tool_input: ToolInput) -> str:
  """
  Saves an uploaded image from the tool input to a local directory.

  This tool iterates through the content parts of the input, finds the first
  image, and saves it to an 'uploads' folder.

  Args:
    tool_input: The input provided to the tool by the ADK framework.

    Returns:
        The GCS URI of the uploaded image or an error message string.
  """
  # Create a directory to store uploads if it doesn't exist
  if not os.path.exists('uploads'):
    os.makedirs('uploads')

  image_part = None
  # Find the first image part in the input
  for part in tool_input.content_parts:
    if part.mime_type and part.mime_type.startswith('image/'):
      image_part = part
      break

  if image_part:
    process_image(part.mime_type,image_part.data)
    # Construct a file path
    file_name = f"uploaded_image.{image_part.mime_type.split('/')[1]}"
    file_path = os.path.join('uploads', file_name)

    # The file data is in the 'data' attribute as bytes
    with open(file_path, 'wb') as f:
      f.write(image_part.data)

    return f"Image successfully saved to {file_path}"
  else:
    return "No image found in the input."
  
  
def process_image(mime_type: str, data: bytes) -> str:
    """Processes and uploads an image to Google Cloud Storage (GCS).

    This function takes image data, writes it to a temporary file,
    and then uploads it to a specified GCS bucket.

    Args:
        mime_type: The MIME type of the image (e.g., "image/png").
        data: The raw byte data of the image.
        prompt: A text prompt describing the desired action for the image.

    Returns:
        The GCS URI of the uploaded image or an error message string.
    """
    image_artifact = types.Part(types.Blob(  mime_type=mime_type,
                                data=data))
    # Check if the uploaded file is an image
    if not image_artifact.mime_type.startswith('image/'):
        return f"Error: Uploaded file is not an image. MIME type: {image_artifact.mime_type}"

    temp_file_path = None
    try:
        # Create a temporary file to store the image bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_artifact.name)[1]) as temp_file:
            temp_file_path = temp_file.name
            image_bytes = image_artifact.read_bytes()
            temp_file.write(image_bytes)
            print(f"Image artifact '{image_artifact.name}' written to temporary file: {temp_file_path}")

        # Call the function to upload the temp file to GCS
        gcs_uri = store_image_artifact_in_gcs(temp_file_path, image_artifact)

        if "Error:" in gcs_uri:
            return f"Failed to upload image to GCS. Reason: {gcs_uri}"

        # --- YOUR INTEGRATION LOGIC GOES HERE ---
        # Now you have the gcs_uri of the uploaded image.
        # You can pass this URI to your other agent tools.
        # For example, you could now call your video_generation_tool.
        print(f"Image GCS URI: {gcs_uri}")
        
        return gcs_uri

    finally:
        # Ensure the temporary file is deleted after the upload attempt
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Temporary file {temp_file_path} deleted.")

