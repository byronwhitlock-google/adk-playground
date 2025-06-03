import uuid
import traceback
import time
import tempfile
import os
import logging
import google.auth
import base64
import asyncio
from urllib.parse import urlparse
from typing import List, Dict
from google.protobuf.duration_pb2 import Duration
from google.cloud.video.transcoder_v1.types import Job
from google.cloud.video import transcoder_v1
from google.cloud.exceptions import NotFound, GoogleCloudError
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
import math # Import math for log10

from tinytag import TinyTag

def get_mp3_audio_duration_gcs(
    audio_uri: str,
) -> str :
    """
    Gets the duration of an MP3 (or potentially WAV with tinytag) audio file stored in Google Cloud Storage
    using a pure Python library (tinytag), without relying on FFmpeg.

    Args:
        audio_uri (str): The GCS URI of the MP3/WAV audio file (e.g., "gs://your-bucket/audio.mp3").

    Returns:
        str: The duration of the audio in seconds, or error message if an error occurs.
    """
    if not audio_uri.startswith("gs://"):
        return(f"Error: Invalid GCS audio URI: {audio_uri}. Input URIs must start with 'gs://'.")
         

    client = storage.Client()
    parsed_uri = urlparse(audio_uri)
    bucket_name = parsed_uri.netloc
    blob_name = parsed_uri.path.lstrip('/')
    
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    temp_file_path = None # Initialize to None for finally block

    try:
        # Check if the blob exists and get its size
        try:
            blob.reload()
        except NotFound:
            return(f"Error: MP3/WAV blob '{blob_name}' not found in bucket '{bucket_name}'. Please check the name and path.")
             
        except GoogleCloudError as e:
            return(f"Google Cloud error checking MP3/WAV blob existence for '{blob_name}': {e}")
            
        except Exception as e:
            return(f"Unexpected error checking MP3/WAV blob existence for '{blob_name}': {e}")
          

        # Create a temporary local file to download the GCS blob
        # Use a more generic extension or detect from blob_name
        file_extension = os.path.splitext(blob_name)[1] if os.path.splitext(blob_name)[1] else ".tmp"
        temp_file_path = f"/tmp/{os.path.basename(blob_name)}{file_extension}"
        
        # Download the entire MP3/WAV file
        try:
            blob.download_to_filename(temp_file_path)
        except GoogleCloudError as e:
            return(f"Google Cloud error during MP3/WAV download of '{blob_name}': {e}")
            
        except Exception as e:
            return(f"Unexpected error during MP3/WAV download of '{blob_name}': {e}")
           

        # Analyze the downloaded MP3/WAV file with tinytag
        try:
            tag = TinyTag.get(temp_file_path)
            duration = tag.duration
            return duration
        except Exception as e:
            return(f"Error extracting duration using tinytag from audio file '{temp_file_path}': {e} This might happen if the file is corrupted or not a valid audio file readable by tinytag.")


    except NotFound as e:
        # This specific NotFound handles cases where the bucket itself might not exist
        return(f"Error: Bucket '{bucket_name}' not found. Details: {e}")
        
    except Exception as e:
        # Catch any other unexpected errors during the process
        return(f"An unexpected error occurred: {e}")
        
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                return(f"Error deleting temporary audio file '{temp_file_path}': {e}")


async def mux_audio(
    video_uri: str,
    audio_uri: str,
    end_time_offset: float,

) -> str:
    """
    Muxes the audio and video streams using the Transcoder API and
    stores the result in GCS. Project ID is inferred from the environment.
    Operates entirely on GCS paths, avoiding local filesystem storage.

    Args:
        video_uri (str): The GCS URI of the video file (e.g., "gs://your-bucket/video.mp4").
        audio_uri (str): The GCS URI of the audio file (e.g., "gs://your-bucket/audio.pcm").
        end_time_offset (float): The end time offset for the muxed output in seconds (must be the minimum of video and audio durations).

                        
    Returns:
        str: The GCS URI of the successfully muxed MP4 file., or error message if failed.

    Raises:
        ValueError: If required URIs are not provided or are invalid, or if project ID cannot be inferred.
        Exception: If the Transcoder job fails or encounters an error.
    """
    
    # hard code bucket
    # TODO: parmaterize this outside the LLM 
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent") # As per user's last snippet

    output_uri_base=f"gs://{bucket_name}/muxed/"

    if not video_uri or not audio_uri:
        raise ValueError("Both 'video_uri' and 'audio_uri' must be provided.")
    if not video_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS video URI: {video_uri}. Input URIs must start with 'gs://'.")
    if not audio_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS audio URI: {audio_uri}. Input URIs must start with 'gs://'.")
    
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") # Default to us-central1 if not set

    
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
    output_filename = uuid.uuid4().hex + ".mp4"
    final_output_uri = f"{output_uri_base}{output_filename}"

    # Use the async client
    client = transcoder_v1.TranscoderServiceAsyncClient()

    # Construct the parent resource path using the inferred project ID and provided location
    parent = f"projects/{project_id}/locations/{location}"

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

