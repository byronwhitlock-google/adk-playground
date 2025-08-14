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


def string_to_webvtt(text_content: str, start_time_seconds: float, end_time_seconds: float) -> str:
    """
    Converts a simple string into a WebVTT formatted string for a specified duration.

    The WebVTT format is a standard for displaying timed text tracks (such as
    subtitles or captions) with HTML5 <track> element.

    Args:
        text_content: The text to be displayed as a caption.
        start_time_seconds: The start time of the caption in seconds.
        end_time_seconds: The end time of the caption in seconds.

    Returns:
        A string formatted in the WebVTT standard.
        Returns an error message string if the end time is not after the start time.
    """
    if end_time_seconds <= start_time_seconds:
        return "Error: End time must be after start time."

    def format_time(seconds: float) -> str:
        """Helper function to convert seconds to HH:MM:SS.mmm format."""
        # Ensure seconds is not negative
        seconds = max(0, seconds)
        
        # Calculate hours, minutes, seconds, and milliseconds
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds * 1000) % 1000)
        
        # Format and return the timestamp string
        return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"

    # Format the start and end times using the helper function
    start_timestamp = format_time(start_time_seconds)
    end_timestamp = format_time(end_time_seconds)

    # Construct the complete WebVTT content
    webvtt_content = (
        "WEBVTT\n\n"
        f"{start_timestamp} --> {end_timestamp}\n"
        f"{text_content}"
    )

    return webvtt_content

async def mux_audio(
    video_uri: str,
    audio_uri: str,
    end_time_offset: float,
    text_stream_content: str ,
) -> str:
    """
    Muxes video, audio, and an optional text stream using the Transcoder API,
    storing the result in GCS. Project ID is inferred from the environment.
    Operates entirely on GCS paths.

    Args:
        video_uri (str): GCS URI of the video file (e.g., "gs://bucket/video.mp4").
        audio_uri (str): GCS URI of the audio file (e.g., "gs://bucket/audio.pcm").
        end_time_offset (float): The end time for the muxed output in seconds.
        text_stream_content (str): A string containing the content for the
                                             subtitle track. The language is hardcoded to "en-US".

    Returns:
        str: The GCS URI of the successfully muxed MP4 file, or an error message.

    Raises:
        ValueError: If required URIs are not provided or are invalid.
        Exception: If the Transcoder job fails.
    """

    # hard code bucket
    # TODO: parmaterize this outside the LLM
    bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET", "byron-alpha-vpagent")

    output_uri_base = f"gs://{bucket_name}/muxed/"
    
    if not video_uri or not audio_uri:
        raise ValueError("Both 'video_uri' and 'audio_uri' must be provided.")
    if not video_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS video URI: {video_uri}.")
    if not audio_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS audio URI: {audio_uri}.")

    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    try:
        credentials, project_id = google.auth.default()
        if not project_id:
            raise ValueError("Could not infer Google Cloud Project ID.")
    except Exception as e:
        raise ValueError(f"Failed to infer Google Cloud Project ID: {e}")

    if not output_uri_base.endswith('/'):
        output_uri_base += '/'

    output_filename = uuid.uuid4().hex + ".mp4"
    final_output_uri = f"{output_uri_base}{output_filename}"

    client = transcoder_v1.TranscoderServiceAsyncClient()
    parent = f"projects/{project_id}/locations/{location}"

    job_config = transcoder_v1.types.Job()
    job_config.output_uri = output_uri_base
    job_config.config = transcoder_v1.types.JobConfig()

    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="video_input_key", uri=video_uri)
    )
    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="audio_input_key", uri=audio_uri)
    )

    edit_atom_inputs = ["video_input_key", "audio_input_key"]
    text_input_key = None
    
    if text_stream_content:
        # Create and upload the subtitle file to GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        subtitle_filename = f"{uuid.uuid4().hex}.srt"
        subtitle_gcs_path = f"text_tracks/{subtitle_filename}" # Store in a subfolder
        blob = bucket.blob(subtitle_gcs_path)

        #srt_content = create_srt_content(text_stream_content, end_time_offset)
        #srt_content=string_to_webvtt(text_stream_content,0,)
        srt_content=string_to_webvtt(text_stream_content,0,end_time_offset)
        blob.upload_from_string(srt_content, content_type='text/plain')
        
        text_track_uri = f"gs://{bucket_name}/{subtitle_gcs_path}"
        
        text_input_key = "text_input_key"
        job_config.config.inputs.append(
            transcoder_v1.types.Input(key=text_input_key, uri=text_track_uri)
        )
        edit_atom_inputs.append(text_input_key)

    end_time_offset_duration = Duration()
    end_time_offset_duration.seconds = int(end_time_offset)
    end_time_offset_duration.nanos = int((end_time_offset - end_time_offset_duration.seconds) * 1e9)

    atom_key = "atom_part_0"
    job_config.config.edit_list.append(
        transcoder_v1.types.EditAtom(
            key=atom_key,
            inputs=edit_atom_inputs,
            start_time_offset=Duration(seconds=0),
            end_time_offset=end_time_offset_duration,
        )
    )

    # Video stream elementary stream
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_video_stream",
            video_stream=transcoder_v1.types.VideoStream(
                h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                    height_pixels=720,
                    width_pixels=1280,
                    bitrate_bps=5000000,
                    frame_rate=30,
                ),
            ),
        )
    )

    # Audio stream elementary stream
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_audio_stream",
            audio_stream=transcoder_v1.types.AudioStream(
                codec="aac",
                bitrate_bps=128000,
            ),
        )
    )

    if text_input_key:
        # FIX: The `TextMapping` object must be used within the `mapping` list.
        job_config.config.elementary_streams.append(
            transcoder_v1.types.ElementaryStream(
                key="output_text_stream",
                text_stream=transcoder_v1.types.TextStream(
                    codec="webvtt",
                    language_code="en-US",
                    display_name="English",
                    mapping_=[
                        transcoder_v1.types.TextStream.TextMapping(
                            atom_key=atom_key,
                            input_key=text_input_key
                        ),
                    ],
                ),
            )
        )
        # As determined previously, the text stream should not be added to the mux_streams for MP4.
        #mux_elementary_streams.append("output_text_stream")

    # job_config.config.mux_streams.append(
    #     transcoder_v1.types.MuxStream(
    #         key="final_mp4_output",
    #         container="mp4",
    #         elementary_streams=["output_video_stream", "output_audio_stream"], # Contains only video and audio
    #         file_name=output_filename,
    #     )
    # )

    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream (
            key="sd-hls-fmp4",
            container="fmp4",
            elementary_streams=["output_video_stream"],
            #file_name=output_filename,
        )
    )

    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream(
            key="audio-hls-fmp4",
            container="fmp4",
            elementary_streams=["output_audio_stream"], # Contains only video and audio
            #file_name=output_filename,
        )
    )
    if text_input_key:
        job_config.config.mux_streams.append(
            transcoder_v1.types.MuxStream(
                    key="text-vtt-en",
                    container="vtt",
                    elementary_streams=["output_text_stream"],
                    segment_settings=transcoder_v1.types.SegmentSettings(
                        segment_duration=Duration(
                            seconds=end_time_offset,
                        ),
                        individual_segments=True,
                    ),
                    # segment_settings=transcoder_v1.types.SegmentSettings(
                    #     segment_duration=duration.Duration(
                    #         seconds=6,
                    #     ),
                    #     individual_segments=True,
                    # ),
            ),
        )
    job_config.config.manifests.append (
        transcoder_v1.types.Manifest(
            file_name="manifest.m3u8",
            type_="HLS",
            mux_streams=[
                "sd-hls-fmp4",
                "audio-hls-fmp4",
                "text-vtt-en",
            ],
        ),
    )
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
                return final_output_uri

            elif response.state == Job.ProcessingState.FAILED:
                error_message = "Unknown error"
                if response.error:
                    error_message = getattr(response.error, 'message', str(response.error))
                raise Exception(f"Transcoder job '{job_name}' failed: {error_message}")

            elif response.state in (Job.ProcessingState.PENDING, Job.ProcessingState.RUNNING, Job.ProcessingState.UNSPECIFIED):
                # Simplified logging for states that just require waiting
                progress_str = ""
                if response.state == Job.ProcessingState.RUNNING and response.progress:
                     progress_str = f" Progress: {response.progress.processed:.1%}"
                print(f"Transcoder job '{job_name}' is {current_state_name}.{progress_str} Waiting...")
            
            else:
                 print(f"Transcoder job '{job_name}' is in an unexpected state: {current_state_name}. Waiting...")


    except Exception as e:
        print(f"\n--- An unexpected error occurred in mux_audio ---")
        print(f"Job Name (if created): {job_name}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        return f"Error: {type(e).__name__} - {e}"