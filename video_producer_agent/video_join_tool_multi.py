
import time
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.types import Job
from google.api_core.exceptions import GoogleAPIError
import asyncio
from typing import List
import google.auth # Import google.auth to infer project ID
import traceback # Import traceback for better error logging

async def video_join_tool(
    location: str,
    input_uris: List[str],
    output_uri_prefix: str,
    output_filename: str,
) -> str:
    """
    Asynchronously joins a list of MP4 files in GCS using the Transcoder API and
    stores the result in GCS. Project ID is inferred from the environment.
    Operates entirely on GCS paths, avoiding local filesystem storage.
    Polls for job completion asynchronously.

    Args:
        location (str): The GCP region for the Transcoder job. Examples: "us-central1",
                        "us-east1", "europe-west1", "asia-southeast1".
                        This cannot be inferred as Transcoder is a regional service.
        input_uris (List[str]): A list of GCS URIs of the input MP4 files
                                (e.g., ["gs://your-bucket/file1.mp4", "gs://your-bucket/file2.mp4"]).
        output_uri_prefix (str): GCS URI prefix for the output directory
                                 (e.g., "gs://your-output-bucket/output-folder/").
                                 The Transcoder API will append generate the output_filename to this prefix.

    Returns:
        str: The GCS URI of the successfully joined MP4 file.

    Raises:
        ValueError: If the input_uris list is empty,  or if project ID cannot be inferred.
        Exception: If the Transcoder job fails or encounters an error.
    """
    if not input_uris:
        raise ValueError("The 'input_uris' list cannot be empty. Please provide at least one input URI.")

    if not location:
        raise ValueError("The 'location' argument cannot be empty.")
    if not output_uri_prefix:
        raise ValueError("The 'output_uri_prefix' argument cannot be empty.")

    # Infer the project ID from the environment
    try:
        credentials, project_id = google.auth.default()
        if not project_id:
            raise ValueError("Could not infer Google Cloud Project ID from the environment. "
                             "Please set GOOGLE_CLOUD_PROJECT environment variable, "
                             "or configure gcloud CLI with 'gcloud config set project <project-id>', "
                             "or ensure your credentials are properly set.")
    except Exception as e:
        raise ValueError(f"Failed to infer Google Cloud Project ID: {e}")

    # Ensure output_uri_prefix ends with a slash for proper GCS path construction
    if not output_uri_prefix.endswith('/'):
        output_uri_prefix += '/'

    # Use the async client
    client = transcoder_v1.TranscoderServiceAsyncClient()

    # Construct the parent resource path using the inferred project ID and provided location
    parent = f"projects/{project_id}/locations/{location}"

    # Define the job configuration
    job_config = transcoder_v1.types.Job() # Renamed for clarity from 'job' to 'job_config'
                                          # to avoid conflict with the Job enum from transcoder_v1.types

    job_config.output_uri = output_uri_prefix # Output prefix for the job
    job_config.config = transcoder_v1.types.JobConfig()

    # Dynamically define inputs with unique keys for each URI in the list
    for i, uri in enumerate(input_uris):
        if not uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {uri}. Input URIs must start with 'gs://'.")
        job_config.config.inputs.append(
            transcoder_v1.types.Input(key=f"video_input_{i}", uri=uri)
        )

        job_config.config.edit_list.append(
            transcoder_v1.types.EditAtom(
                key=f"atom_part{i}",
                inputs=[f"video_input_{i}"], # Reference the input with its generated key
                # For concatenation, start_time_offset and end_time_offset should typically be 0
                # to include the entire clip. If you need to trim, adjust these.
                # For simplicity, we assume full clip concatenation.
                # start_time_offset="0s", # Start from beginning of input
                # end_time_offset="0s"    # End at the end of input (0s implies full duration)
            )
        )

    # Define elementary streams (encoding settings for video and audio tracks).
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_video_stream",
            video_stream=transcoder_v1.types.VideoStream(
                h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                    height_pixels=360,    # Example: 360p
                    width_pixels=640,     # Example: 360p
                    bitrate_bps=550000,   # Example: 550 kbps
                    frame_rate=30,        # Example: 30 fps
                ),
            ),
        )
    )
    # --- IF YOU NEED AUDIO, UNCOMMENT AND CONFIGURE THIS SECTION ---
    # job_config.config.elementary_streams.append(
    #     transcoder_v1.types.ElementaryStream(
    #         key="output_audio_stream",
    #         audio_stream=transcoder_v1.types.AudioStream(
    #             codec="aac", # Common audio codec
    #             bitrate_bps=128000, # Example: 128 kbps
    #         ),
    #     )
    # )
    # -------------------------------------------------------------

    # Define mux streams (how elementary streams are combined into output containers).
    mux_elementary_streams = ["output_video_stream"]#, "output_audio_stream"] # Include audio if uncommented above
    # --- IF YOU DID NOT UNCOMMENT THE AUDIO STREAM ABOVE, REMOVE "output_audio_stream" from the list above ---
    # Example if only video: mux_elementary_streams = ["output_video_stream"]
    # -------------------------------------------------------------

    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream(
            key="final_mp4_output",
            container="mp4",
            elementary_streams=mux_elementary_streams,
            file_name= f"output_video_{int(time.time())}.mp4", # The actual filename within the output_uri_prefix folder
        )
    )

    # Set job retention policy to a default of 1 day after completion
    job_config.ttl_after_completion_days = 1 # Default to 1 day

    #print(f"Creating Transcoder job for concatenation with config: {job_config}")
    job_name = None # Initialize job_name
    try:
        # Asynchronously send the job creation request
        create_job_response = await client.create_job(parent=parent, job=job_config)
        job_name = create_job_response.name
        print(f"Transcoder job created: {job_name}")

        # Asynchronously poll for job completion
        while True:
            await asyncio.sleep(15) # Polling interval (e.g., 15 seconds)
            print(f"Polling status for job {job_name}...")
            response = await client.get_job(name=job_name)
            current_state_name = Job.ProcessingState(response.state).name # Get enum name
            print(f"Job status: {current_state_name}")

            if response.state == Job.ProcessingState.SUCCEEDED:
                print(f"Transcoder job '{job_name}' succeeded.")
                # Return the full GCS URI of the joined file
                return f"{output_uri_prefix}{output_filename}"

            elif response.state == Job.ProcessingState.FAILED:
                error_message = "Unknown error"
                error_details_str = ""
                if response.error:
                    error_message = getattr(response.error, 'message', str(response.error))
                    details_list = getattr(response.error, 'details', [])
                    if details_list:
                         error_details_str = f" | Details: {details_list}"
                raise Exception(f"Transcoder job '{job_name}' failed: {error_message}{error_details_str}")

            elif response.state == Job.ProcessingState.PENDING:
                 print(f"Transcoder job '{job_name}' is PENDING. Waiting...")
                 # Continue polling

            elif response.state == Job.ProcessingState.RUNNING:
                 progress = getattr(response, 'progress', None)
                 progress_percent_str = "N/A"
                 if progress and hasattr(progress, 'analyzed') and hasattr(progress, 'encoded') and hasattr(progress, 'uploaded') and hasattr(progress, 'notified'):
                     # A more detailed progress might be available depending on the job type
                     # For simple concatenation, 'processed' might not be directly populated
                     # We can estimate based on other flags or just indicate it's running.
                     # The 'progress' object structure can vary.
                     # Example: progress_percent_str = f"Analyzed: {progress.analyzed}, Encoded: {progress.encoded}"
                     pass # Keep it simple for now
                 elif progress and hasattr(progress, 'processed') and progress.processed is not None:
                     progress_percent_str = f"{progress.processed:.1%}"

                 print(f"Transcoder job '{job_name}' is RUNNING. Progress: {progress_percent_str}. Waiting...")
                 # Continue polling
            
            elif response.state == Job.ProcessingState.UNSPECIFIED:
                print(f"Transcoder job '{job_name}' is in an UNSPECIFIED state. Waiting...")
                # Continue polling, but this might indicate an issue if it persists.

            else:
                # This case should ideally not be reached if all defined states are handled.
                print(f"Transcoder job '{job_name}' is in an unexpected state: {current_state_name}. Waiting...")
                # Continue polling


    except GoogleAPIError as e:
        print(f"Google Cloud API Error occurred for job '{job_name or 'creation'}': {e}")
        raise
    except Exception as e:
        print(f"\n--- An unexpected error occurred in video_join_tool ---")
        print(f"Job Name (if created): {job_name}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Traceback:")
        traceback.print_exc()
        print("--- End of error details ---\n")
        raise e

# --- Example Usage (async context required) ---
async def main():
    """Example of how to run the video_join_tool."""
    try:
        # --- IMPORTANT: Replace with your actual values or ensure environment variables are set ---
        gcp_project_id = "your-gcp-project-id" # Replace or ensure GOOGLE_CLOUD_PROJECT is set
        gcp_location = "us-central1"          # Replace with your desired GCP region

        # Example input files in GCS (ensure these exist and your service account has access)
        input_video_uris = [
            f"gs://{gcp_project_id}-my-videos/input_segment_01.mp4", # Replace with your bucket and files
            f"gs://{gcp_project_id}-my-videos/input_segment_02.mp4"  # Replace with your bucket and files
        ]
        # Example output location in GCS (ensure the bucket exists and your service account has write access)
        output_gcs_prefix = f"gs://{gcp_project_id}-my-videos-output/concatenated/" # Replace with your bucket
        output_file_name = "final_concatenated_video.mp4"
        # --- End of values to replace ---


        # Set the project ID environment variable if not already set for google.auth.default()
        # import os
        # if "GOOGLE_CLOUD_PROJECT" not in os.environ:
        #     os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_project_id


        print(f"Starting video join process...")
        print(f"Project ID (inferred/set): {google.auth.default()[1]}") # Verify inferred project ID
        print(f"Location: {gcp_location}")
        print(f"Input URIs: {input_video_uris}")
        print(f"Output Prefix: {output_gcs_prefix}")
        print(f"Output Filename: {output_file_name}")


        output_gcs_path = await video_join_tool(
            location=gcp_location,
            input_uris=input_video_uris,
            output_uri_prefix=output_gcs_prefix,
            output_filename=output_file_name,
        )
        print(f"\nSuccessfully joined videos. Output available at: {output_gcs_path}")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except GoogleAPIError as gae:
        print(f"Google API Error during video joining: {gae}")
    except Exception as ex:
        print(f"An unexpected error occurred during video joining: {ex}")
        traceback.print_exc()