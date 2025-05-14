import time
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.types import Job
from google.api_core.exceptions import GoogleAPIError
import asyncio
from typing import List, Dict
import google.auth # Import google.auth to infer project ID
import traceback # Import traceback for better error logging

async def video_join_tool(
    location: str,
    input_streams: List[Dict[str, str]], # Updated to accept a list of dictionaries with video_uri and audio_uri
    output_uri_prefix: str,
    output_filename: str,
) -> str:
    """
    Asynchronously joins a list of video and audio files in GCS using the Transcoder API and
    stores the result in GCS. Project ID is inferred from the environment.
    Operates entirely on GCS paths, avoiding local filesystem storage.
    Polls for job completion asynchronously.

    Args:
        location (str): The GCP region for the Transcoder job. Examples: "us-central1",
                        "us-east1", "europe-west1", "asia-southeast1".
                        This cannot be inferred as Transcoder is a regional service.
        input_streams (List[Dict[str, str]]): A list of dictionaries, each containing
                                             'video_uri' and 'audio_uri' (e.g.,
                                             [{'video_uri': 'gs://your-bucket/video1.mp4',
                                               'audio_uri': 'gs://your-bucket/audio1.linear16'}, ...]).
                                             The video stream is expected to be an MP4 video,
                                             and the audio stream is expected to be Linear16 PCM.
        output_uri_prefix (str): GCS URI prefix for the output directory
                                 (e.g., "gs://your-output-bucket/output-folder/").
                                 The Transcoder API will append the generated output_filename to this prefix.
        output_filename (str): The desired filename for the output MP4 file.

    Returns:
        str: The GCS URI of the successfully joined MP4 file.

    Raises:
        ValueError: If the input_streams list is empty, or if project ID cannot be inferred,
                    or if URIs are invalid.
        Exception: If the Transcoder job fails or encounters an error.
    """
    if not input_streams:
        raise ValueError("The 'input_streams' list cannot be empty. Please provide at least one input stream pair.")

    if not location:
        raise ValueError("The 'location' argument cannot be empty.")
    if not output_uri_prefix:
        raise ValueError("The 'output_uri_prefix' argument cannot be empty.")
    if not output_filename:
        raise ValueError("The 'output_filename' argument cannot be empty.")

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
    job_config = transcoder_v1.types.Job()
    job_config.output_uri = output_uri_prefix
    job_config.config = transcoder_v1.types.JobConfig()

    # Dynamically define inputs with unique keys for each video and audio URI in the list
    for i, stream_pair in enumerate(input_streams):
        video_uri = stream_pair.get('video_uri')
        audio_uri = stream_pair.get('audio_uri')

        if not video_uri or not audio_uri:
            raise ValueError(f"Input stream pair at index {i} is missing 'video_uri' or 'audio_uri'.")

        if not video_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS video URI: {video_uri}. Input URIs must start with 'gs://'.")
        if not audio_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS audio URI: {audio_uri}. Input URIs must start with 'gs://'.")

        video_input_key = f"video_input_{i}"
        audio_input_key = f"audio_input_{i}"

        job_config.config.inputs.append(
            transcoder_v1.types.Input(key=video_input_key, uri=video_uri)
        )
        job_config.config.inputs.append(
            transcoder_v1.types.Input(key=audio_input_key, uri=audio_uri)
        )

        # Define edit list for concatenation, referencing both video and audio inputs
        job_config.config.edit_list.append(
            transcoder_v1.types.EditAtom(
                key=f"atom_part_{i}",
                inputs=[video_input_key, audio_input_key],
            )
        )

    # Define elementary streams (encoding settings for video and audio tracks).
    # Video stream (assuming m4p implies standard MP4 video, using H264)
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

    # Audio stream (Linear16 corresponds to PCM_S16)
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_audio_stream",
            audio_stream=transcoder_v1.types.AudioStream(
                codec="pcm_s16be", # Linear16 is typically PCM_S16 Big Endian
                bitrate_bps=256000, # Example: 256 kbps for high quality linear PCM
                sample_rate_hertz=48000, # Example: 48 kHz
                channels=2, # Example: Stereo
            ),
        )
    )

    # Define mux streams (how elementary streams are combined into output containers).
    mux_elementary_streams = ["output_video_stream", "output_audio_stream"]

    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream(
            key="final_mp4_output",
            container="mp4",
            elementary_streams=mux_elementary_streams,
            file_name= output_filename, # The actual filename within the output_uri_prefix folder
        )
    )

    # Set job retention policy to a default of 1 day after completion
    job_config.ttl_after_completion_days = 1

    job_name = None
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
            current_state_name = Job.ProcessingState(response.state).name
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