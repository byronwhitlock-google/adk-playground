import time
import uuid
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.types import Job
from google.api_core.exceptions import GoogleAPIError
import asyncio
from typing import List
import google.auth # Import google.auth to infer project ID
import traceback # Import traceback for better error logging


async def video_join_tool(
    location: str,
    input_uris: List[str]
) -> str:
    """
    Asynchronously joins a list of MP4 files in GCS using the Transcoder API and
    stores the result in GCS. This updated version now **concatenates both
    video and audio streams** from the source files into the destination.
    All input_URIs must have valid audio streams from mux_audio.

    Args:
        location (str): The GCP region for the Transcoder job. Examples: "us-central1",
                        "us-east1", "europe-west1", "asia-southeast1".
                        This cannot be inferred as Transcoder is a regional service.
        input_uris (List[str]): A list of GCS URIs of the input MP4 files
                                (e.g., ["gs://your-bucket/file1.mp4", "gs://your-bucket/file2.mp4"]).
        
    Returns:
        str: The GCS URI of the successfully joined MP4 file. or string error message

    Raises:
        ValueError: If the input_uris list is empty, or if project ID cannot be inferred.
        Exception: If the Transcoder job fails or encounters an error.
    """
    if not input_uris:
        raise ValueError("The 'input_uris' list cannot be empty. Please provide at least one input URI.")

    if not location:
        raise ValueError("The 'location' argument cannot be empty.")
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

    # hard code bucket
    # TODO: parmaterize this outside the LLM 
    output_uri_prefix="gs://byron-alpha-vpagent/commercials/"


    # Ensure output_uri_prefix ends with a slash for proper GCS path construction
    if not output_uri_prefix.endswith('/'):
        output_uri_prefix += '/'
    
    output_filename = uuid.uuid4().hex + ".mp4"


    # Use the async client
    client = transcoder_v1.TranscoderServiceAsyncClient()

    # Construct the parent resource path using the inferred project ID and provided location
    parent = f"projects/{project_id}/locations/{location}"

    # Define the job configuration
    job_config = transcoder_v1.types.Job()
    job_config.output_uri = output_uri_prefix
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
                inputs=[f"video_input_{i}"],
            )
        )

    # Define elementary streams (encoding settings for video and audio tracks).
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_video_stream",
            video_stream=transcoder_v1.types.VideoStream(
                h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                    height_pixels=360,
                    width_pixels=640,
                    bitrate_bps=550000,
                    frame_rate=30,
                ),
            ),
        )
    )

    # --- ADDED: AUDIO STREAM CONFIGURATION ---
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_audio_stream",
            audio_stream=transcoder_v1.types.AudioStream(
                codec="aac",  # Common audio codec
                bitrate_bps=128000, # Example: 128 kbps
                channel_count=2, # Example: Stereo audio
            ),
        )
    )
    # ------------------------------------------

    # Define mux streams (how elementary streams are combined into output containers).
    # --- UPDATED: INCLUDE AUDIO STREAM IN MUX ---
    mux_elementary_streams = ["output_video_stream", "output_audio_stream"]
    # --------------------------------------------

    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream(
            key="final_mp4_output",
            container="mp4",
            elementary_streams=mux_elementary_streams,
            file_name=output_filename, # Use the provided output_filename
        )
    )

    # Set job retention policy to a default of 1 day after completion
    job_config.ttl_after_completion_days = 1

    job_name = None
    try:
        create_job_response = await client.create_job(parent=parent, job=job_config)
        job_name = create_job_response.name
        print(f"Transcoder job created: {job_name}")

        while True:
            await asyncio.sleep(15)
            print(f"Polling status for job {job_name}...")
            response = await client.get_job(name=job_name)
            current_state_name = Job.ProcessingState(response.state).name
            print(f"Job status: {current_state_name}")

            if response.state == Job.ProcessingState.SUCCEEDED:
                print(f"Transcoder job '{job_name}' succeeded.")
                return f"{output_uri_prefix}{output_filename}"

            elif response.state == Job.ProcessingState.FAILED:
                error_message = "Unknown error"
                error_details_str = ""
                if response.error:
                    error_message = getattr(response.error, 'message', str(response.error))
                    details_list = getattr(response.error, 'details', [])
                    if details_list:
                         error_details_str = f" | Details: {details_list}"
                return (f"Transcoder job '{job_name}' failed: {error_message}{error_details_str}")

            elif response.state == Job.ProcessingState.PENDING:
                 print(f"Transcoder job '{job_name}' is PENDING. Waiting...")

            elif response.state == Job.ProcessingState.RUNNING:
                 progress = getattr(response, 'progress', None)
                 progress_percent_str = "N/A"
                 if progress and hasattr(progress, 'processed') and progress.processed is not None:
                     progress_percent_str = f"{progress.processed:.1%}"
                 print(f"Transcoder job '{job_name}' is RUNNING. Progress: {progress_percent_str}. Waiting...")
            
            elif response.state == Job.ProcessingState.UNSPECIFIED:
                print(f"Transcoder job '{job_name}' is in an UNSPECIFIED state. Waiting...")

            else:
                print(f"Transcoder job '{job_name}' is in an unexpected state: {current_state_name}. Waiting...")

    except GoogleAPIError as e:
        return(f"Google Cloud API Error occurred for job '{job_name or 'creation'}': {e}")
        
    except Exception as e:
        print(f"\n--- An unexpected error occurred in video_join_tool ---")
        print(f"Job Name (if created): {job_name}")
        print(f"Error Type: {type(e).__name__}")
        return(f"Error Message: {e}")
        print("Traceback:")
        traceback.print_exc()
        print("--- End of error details ---\n")
        raise e