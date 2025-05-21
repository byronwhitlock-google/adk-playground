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



async def mux_music(
    video_with_audio_uri: str,
    music_uri: str,
    start_time_offset_music: float,
    volume_music: float,
    location: str,
    music_duration: float,
    main_video_duration: float
) -> str:
    """
    Muxes a WAV audio file as background music into an existing MP4 file
    (which already contains video and audio streams) using the Transcoder API.
    The music stream is truncated at the end of the existing MP4's duration.
    Project ID is inferred from the environment.

    Args:
        video_with_audio_uri (str): The GCS URI of the input MP4 file
                                     (e.g., "gs://your-bucket/input_video.mp4").
        music_uri (str): The GCS URI of the WAV music file
                         (e.g., "gs://your-bucket/background_music.wav").
        start_time_offset_music (float): The time in seconds where the music
                                         should start playing in the output.
        volume_music (float): The volume of the music track (0.0 to 1.0, where 1.0 is full volume).
        location (str): The GCP region for the Transcoder job.
        music_duration (float): The duration of the music track in seconds.
        main_video_duration (float): The duration of the main video track in seconds.


    Returns:
        str: The GCS URI of the successfully muxed MP4 file with background music,
             or an error message if failed.

    Raises:
        ValueError: If required URIs are not provided or are invalid,
                    or if project ID cannot be inferred.
        Exception: If the Transcoder job fails or encounters an error.
    """

    output_uri_base = "gs://byron-alpha-vpagent/muxed_music/" # Dedicated output folder

    if not video_with_audio_uri or not music_uri:
        raise ValueError("Both 'video_with_audio_uri' and 'music_uri' must be provided.")
    if not video_with_audio_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS video URI: {video_with_audio_uri}. Input URIs must start with 'gs://'.")
    if not music_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS music URI: {music_uri}. Input URIs must start with 'gs://'.")
    if not location:
        raise ValueError("The 'location' argument cannot be empty.")
    if not 0.0 <= volume_music <= 1.0:
        raise ValueError("Volume must be between 0.0 and 1.0.")

    try:
        credentials, project_id = google.auth.default()
        if not project_id:
            raise ValueError("Could not infer Google Cloud Project ID from the environment.")
    except Exception as e:
        raise ValueError(f"Failed to infer Google Cloud Project ID: {e}")

    if not output_uri_base.endswith('/'):
        output_uri_base += '/'

    output_filename = uuid.uuid4().hex + "_with_music.mp4"
    final_output_uri = f"{output_uri_base}{output_filename}"

    client = transcoder_v1.TranscoderServiceAsyncClient()
    parent = f"projects/{project_id}/locations/{location}"

    # print(f"Getting duration for main video: {video_with_audio_uri}")
    # main_video_duration = await get_media_duration(client, project_id, location, video_with_audio_uri)
    # print(f"Main video duration: {main_video_duration:.2f}s")

    # print(f"Getting duration for music: {music_uri}")
    # music_duration_str = get_mp3_audio_duration_gcs(music_uri)
    # if isinstance(music_duration_str, str) and music_duration_str.startswith("Error"):
    #     raise Exception(f"Failed to get music duration: {music_duration_str}")
    # music_duration = float(music_duration_str)
    # print(f"Music duration: {music_duration:.2f}s")

    job_config = transcoder_v1.types.Job()
    job_config.output_uri = output_uri_base
    job_config.config = transcoder_v1.types.JobConfig()

    # Define the main input (MP4 with existing video and audio)
    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="main_input", uri=video_with_audio_uri)
    )
    # Define the music input (WAV file)
    job_config.config.inputs.append(
        transcoder_v1.types.Input(key="music_input", uri=music_uri)
    )

    # Convert start_time_offset_music to Duration
    start_offset_music_duration = Duration()
    start_offset_music_duration.seconds = int(start_time_offset_music)
    start_offset_music_duration.nanos = int((start_time_offset_music - start_offset_music_duration.seconds) * 1e9)

    # Calculate the effective end time for the music stream
    # It should end at the minimum of its own natural end or the main video's end
    effective_music_end_time = min(start_time_offset_music + music_duration, main_video_duration)

    # Convert effective_music_end_time to Duration
    effective_music_end_time_duration = Duration()
    effective_music_end_time_duration.seconds = int(effective_music_end_time)
    effective_music_end_time_duration.nanos = int((effective_music_end_time - effective_music_end_time_duration.seconds) * 1e9)


    # Edit list to include both the main video/audio and the music.
    # Main video and audio atom (references all existing streams from "main_input")
    job_config.config.edit_list.append(
        transcoder_v1.types.EditAtom(
            key="main_content_atom",
            inputs=["main_input","music_input"],
            # Explicitly set end_time_offset for main content to its full duration
            # This ensures the main content is not truncated if the music is shorter
            start_time_offset=Duration(seconds=0),
            end_time_offset=Duration(seconds=int(main_video_duration),
                                     nanos=int((main_video_duration - int(main_video_duration)) * 1e9))
        )
    )

    # Elementary streams for video (from main input)
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_video_stream",
            video_stream=transcoder_v1.types.VideoStream(
                h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                    # height_pixels=720,
                    # width_pixels=1280,
                    bitrate_bps=15000000,
                    frame_rate=30,
                ),
            ),
        )
    )

    # Elementary stream for the *original* audio (from main input)
    job_config.config.elementary_streams.append(
        transcoder_v1.types.ElementaryStream(
            key="output_audio_stream",
            audio_stream=transcoder_v1.types.AudioStream(
                codec="mp3",
                bitrate_bps=128000,
                sample_rate_hertz=48000,
                channel_count=2,
                # mapping_=[ 
                #     transcoder_v1.types.AudioStream.AudioMapping (
                #         atom_key="main_content_atom", # Reference the music edit atom
                #         input_key="main_input"
                #     ), 
                #     transcoder_v1.types.AudioStream.AudioMapping (
                #         atom_key="music_atom", # Reference the music edit atom
                #         input_key="music_input",
                #         input_channel=0,
                #         output_channel=0,
                #         gain_db=(20 * math.log10(volume_music)) if volume_music > 0 else -100 # Apply volume
                #     ), 
                #     transcoder_v1.types.AudioStream.AudioMapping (
                #         atom_key="music_atom", # Reference the music edit atom
                #         input_key="music_input",
                #         input_channel=1,
                #         output_channel=1,
                #         gain_db=(20 * math.log10(volume_music)) if volume_music > 0 else -100 # Apply volume
                #     ), 
                # ]


                    
                #     transcoder_v1.types.AudioStream.AudioMapping (
                #         atom_key="music_atom", # Reference the music edit atom
                #         input_key="music_input",
                #         input_track=0,
                #         input_channel=0,
                #         output_channel=2,
                #         gain_db=(20 * math.log10(volume_music)) if volume_music > 0 else -100 # Apply volume
                #     ),
                # ]
            ),
        )
    )
    
    # Mux streams: Combine video, original audio, and new music audio
    job_config.config.mux_streams.append(
        transcoder_v1.types.MuxStream(
            key="final_mp4_output",
            container="mp4",
            elementary_streams=[
                "output_video_stream",
                "output_audio_stream",
               # "output_music_audio_stream"
            ],
            file_name=output_filename,
        )
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
                error_details_str = ""
                if response.error:
                    error_message = getattr(response.error, 'message', str(response.error))
                    details_list = getattr(response.error, 'details', [])
                    if details_list:
                         error_details_str = f" | Details: {details_list}"
                raise Exception(f"Transcoder job '{job_name}' failed: {error_message}{error_details_str}")
            # Add other states for more informative polling messages
            elif response.state == Job.ProcessingState.PENDING:
                print(f"Transcoder job '{job_name}' is PENDING. Waiting...")
            elif response.state == Job.ProcessingState.RUNNING:
                progress = getattr(response, 'progress', None)
                progress_percent_str = "N/A"
                if progress and hasattr(progress, 'processed') and progress.processed is not None:
                    progress_percent_str = f"{progress.processed:.1%}"
                print(f"Transcoder job '{job_name}' is RUNNING. Progress: {progress_percent_str}. Waiting...")
            else:
                print(f"Transcoder job '{job_name}' is in an unexpected state: {current_state_name}. Waiting...")

    except Exception as e:
        print(f"\n--- An unexpected error occurred in mux_music ---")
        print(f"Job Name (if created): {job_name}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        # traceback.print_exc() # Uncomment for full traceback during debugging
        print("--- End of error details ---\n")
        return f"Error: {type(e).__name__} - {e}"