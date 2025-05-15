import time
from urllib.parse import urlparse
from google.cloud.video import transcoder_v1
from google.cloud.video.transcoder_v1.types import Job # Corrected import for MediaAnalysis
from google.api_core.exceptions import GoogleAPIError




import asyncio
from typing import List, Dict
import google.auth # Import google.auth to infer project ID
import traceback # Import traceback for better error logging
from google.protobuf.duration_pb2 import Duration # Import Duration type for time offsets
import base64 # Required for base64 encoding the mediaAnalysis ID

import os
from google.cloud import storage

def get_linear16_audio_duration_gcs(
    audio_uri: str,
) -> float:
    """
    Gets the duration of a LINEAR16 audio file stored in Google Cloud Storage.

    LINEAR16 is 16-bit signed PCM, so bit_depth is implicitly 16.

    Args:
        bucket_name (str): The name of your GCS bucket.
        blob_name (str): The path to the LINEAR16 audio file in the bucket
                         (e.g., 'audio/my_linear16_recording.raw').
        sample_rate (int): The sample rate of the audio (e.g., 16000 Hz, 44100 Hz).
        num_channels (int): The number of audio channels (e.g., 1 for mono, 2 for stereo).

    Returns:
        float: The duration of the audio in seconds.
    """
    #defaults from text to speech tool
    sample_rate=22500
    num_channels=1

    if not audio_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS audio URI: {audio_uri}. Input URIs must start with 'gs://'.")
    client = storage.Client()
    parsed_uri = urlparse(audio_uri)
    bucket_name = parsed_uri.netloc
    blob_name = parsed_uri.path.lstrip('/')
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    

    

    # Create a temporary local file to download the GCS blob
    temp_file_path = f"/tmp/{os.path.basename(blob_name)}"
    blob.download_to_filename(temp_file_path)

    duration_seconds = 0.0
    bit_depth = 16 # LINEAR16 explicitly means 16-bit

    try:
        bytes_per_sample = bit_depth // 8  # 16 bits / 8 bits/byte = 2 bytes
        bytes_per_frame = bytes_per_sample * num_channels

        file_size_bytes = os.path.getsize(temp_file_path)

        if bytes_per_frame > 0:
            total_samples = file_size_bytes // bytes_per_frame
            duration_seconds = total_samples / float(sample_rate)
        else:
            print(f"Warning: bytes_per_frame is 0. Check num_channels for {blob_name}.")

    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

    return duration_seconds
  
async def mux_audio(
    video_uri: str,
    audio_uri: str,
    end_time_offset: float,
    output_uri_base: str,
    location: str,
) -> str:
    """
    Muxes the audio and video streams using the Transcoder API and
    stores the result in GCS. Project ID is inferred from the environment.
    Operates entirely on GCS paths, avoiding local filesystem storage.

    Args:
        video_uri (str): The GCS URI of the video file (e.g., "gs://your-bucket/video.mp4").
        audio_uri (str): The GCS URI of the audio file (e.g., "gs://your-bucket/audio.pcm").
        end_time_offset (float): The end time offset for the muxed output in seconds (must be the minimum of video and audio durations).
        output_uri_base (str): GCS URI prefix for the output directory
                                  (e.g., "gs://your-output-bucket/output-folder/").
        location (str): The GCP region for the Transcoder job. Examples: "us-central1",
                        "us-east1", "europe-west1", "asia-southeast1".
                        
    Returns:
        str: The GCS URI of the successfully muxed MP4 file., or error message if failed.

    Raises:
        ValueError: If required URIs are not provided or are invalid, or if project ID cannot be inferred.
        Exception: If the Transcoder job fails or encounters an error.
    """

    if not video_uri or not audio_uri:
        raise ValueError("Both 'video_uri' and 'audio_uri' must be provided.")
    if not video_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS video URI: {video_uri}. Input URIs must start with 'gs://'.")
    if not audio_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS audio URI: {audio_uri}. Input URIs must start with 'gs://'.")
    if not output_uri_base:
        raise ValueError("The 'output_uri_base' argument cannot be empty.")
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

    # Ensure output_uri_base ends with a slash for proper GCS path construction
    if not output_uri_base.endswith('/'):
        output_uri_base += '/'
    
    # Generate a unique output filename for the muxed file
    output_filename = f"muxed_output_{int(time.time())}.mp4"
    final_output_uri = f"{output_uri_base}{output_filename}"

    # Use the async client
    client = transcoder_v1.TranscoderServiceAsyncClient()

    # Construct the parent resource path using the inferred project ID and provided location
    parent = f"projects/{project_id}/locations/{location}"

    # --- Get durations of input video and audio ---
    print(f"Getting duration for video: {video_uri}")
    video_duration = 8.0# await get_media_duration(client, project_id, location, video_uri)
    print(f"Video duration: {video_duration:.2f}s")

    #print(f"Getting duration for audio: {audio_uri}")
    audio_duration =  get_linear16_audio_duration_gcs(audio_uri) #await get_media_duration(client, project_id, location, audio_uri)
    print(f"Audio duration: {audio_duration:.2f}s")

    # The atom's effective duration should be the minimum of its component streams
    atom_duration = min(video_duration, audio_duration)
    print(f"Using atom duration: {atom_duration:.2f}s (min of video and audio)")
    # --- End duration fetching ---

    # Define the job configuration
    job_config = transcoder_v1.types.Job()
    job_config.output_uri = output_uri_base # This is the base path
    job_config.config = transcoder_v1.types.JobConfig()

    # Define inputs with unique keys for the video and audio URIs
    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="video_input_key", uri=video_uri)
    )
    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="audio_input_key", uri=audio_uri)
    )

    # calucualte the google proto duration from a float
    end_time_offset_duration = Duration()
    end_time_offset_duration.seconds = int(end_time_offset)
    nanoseconds = int((end_time_offset - end_time_offset_duration.seconds) * 1e9)
    end_time_offset_duration.nanos = nanoseconds

    # Define edit list for muxing, referencing both video and audio inputs
    # Explicitly set start_time_offset and end_time_offset
    job_config.config.edit_list.append(
        transcoder_v1.types.EditAtom(
            key="atom_part_0", # Single atom for muxing
            inputs=["video_input_key", "audio_input_key"],
            start_time_offset=Duration(seconds=0),
            end_time_offset=end_time_offset_duration,
          #  end_time_offset=Duration(seconds=int(atom_duration), nanos=int((atom_duration - int(atom_duration)) * 1e9)),
        )
    )

    # Define elementary streams (encoding settings for video and audio tracks).
    # Video stream (using H264 for MP4 output)
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_video_stream",
            video_stream=transcoder_v1.types.VideoStream(
                h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                    height_pixels=720,    # Example: 720p (HD) - adjust as needed
                    width_pixels=1280,    # Example: 720p (HD) - adjust as needed
                    bitrate_bps=5000000,  # Example: 5 Mbps for HD video
                    frame_rate=30,        # Example: 30 fps
                    # Other H264 settings can be added here if needed, e.g., preset, crf_level
                ),
            ),
        )
    )

    # Audio stream (transcoding to AAC for MP4 output)
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_audio_stream",
            audio_stream=transcoder_v1.types.AudioStream(
                codec="aac", # Recommended for MP4 output
                bitrate_bps=128000, # Example: 128 kbps for AAC audio
                sample_rate_hertz=48000, # Example: 48 kHz
                channel_count=2, # Example: Stereo
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
            file_name=output_filename, # The actual filename within the output_uri_base folder
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
                # Return the full GCS URI of the muxed file
                return final_output_uri

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

    except Exception as e:
        print(f"\n--- An unexpected error occurred in mux_audio ---")
        print(f"Job Name (if created): {job_name}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
      #  print("Traceback:")
      #  traceback.print_exc()
        print("--- End of error details ---\n")
       # raise e
        return f"Error: {type(e).__name__} - {e}"