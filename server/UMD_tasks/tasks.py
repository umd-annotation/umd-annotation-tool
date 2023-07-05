from contextlib import suppress
import json
import os
from pathlib import Path
import shutil
import subprocess
from subprocess import Popen
from sys import meta_path
import tempfile
from typing import Dict, List, Optional, Tuple
from urllib import request
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from GPUtil import getGPUs
from PIL import Image
from girder_client import GirderClient
from girder_worker.app import app
from girder_worker.task import Task
from girder_worker.utils import JobManager, JobStatus

from UMD_tasks import constants, utils


def get_gpu_environment() -> Dict[str, str]:
    """Get environment variables for using CUDA enabled GPUs."""
    env = os.environ.copy()

    gpu_uuid = env.get("WORKER_GPU_UUID")
    gpus = [gpu.id for gpu in getGPUs() if gpu.uuid == gpu_uuid]

    # Only set this env var if WORKER_GPU_UUID was supplied,
    # and it matches an installed GPU
    if gpus:
        env["CUDA_VISIBLE_DEVICES"] = str(gpus[0])

    return env


class Config:
    def __init__(self):
        self.gpu_process_env = get_gpu_environment()


@app.task(bind=True, acks_late=True)
def generate_splits(
    self: Task,
    folderId: str,
    itemId: str,
    user_id: str,
    user_login: str,
):
    context: dict = {}
    gc: GirderClient = self.girder_client
    manager: JobManager = self.job_manager
    if utils.check_canceled(self, context):
        manager.updateStatus(JobStatus.CANCELED)
        return

    folderData = gc.getFolder(folderId)

    with tempfile.TemporaryDirectory() as _working_directory, suppress(utils.CanceledError):
        _working_directory_path = Path(_working_directory)
        item = gc.getItem(itemId)
        file_name = str(_working_directory_path / item['name'])
        manager.write(f'Fetching input from {itemId} to {file_name}...\n')
        gc.downloadItem(itemId, _working_directory_path, name=item.get('name'))

        command = [
            "ffprobe",
            "-print_format",
            "json",
            "-v",
            "quiet",
            "-show_format",
            "-show_streams",
            file_name,
        ]
        stdout = utils.stream_subprocess(
            self, context, manager, {'args': command}, keep_stdout=True
        )
        jsoninfo = json.loads(stdout)
        videostream = list(filter(lambda x: x["codec_type"] == "video", jsoninfo["streams"]))
        avgFpsString: str = videostream[0]["avg_frame_rate"]
        originalFps = None
        if avgFpsString:
            dividend, divisor = [int(v) for v in avgFpsString.split('/')]
            originalFps = dividend / divisor
        if originalFps != 30:
            print(f'Warning the video file: {file_name} does not have a FPS of 30')
        width = int(videostream[0]['width'])
        height = int(videostream[0]['height'])
        framecount = int(videostream[0]['nb_frames'])
        start_buffer = 5.0
        segment_length = 15.0
        start = originalFps * start_buffer

        current_frame = start
        tracks = {}
        track_count = 0
        while current_frame < framecount:
            endframe = current_frame + (segment_length * originalFps)
            if framecount - (current_frame + (segment_length * originalFps)) < originalFps * segment_length:
                # Now we need to extend the last frame to fill the remaining time
                endframe = framecount
            end = min(framecount, endframe)
            tracks[track_count] = {
                "begin": current_frame,
                "end": end,
                "confidencePairs": [["segment", 1.0]],
                "attributes": {},
                "id": track_count,
                "features": [
                    {
                        "bounds": [0, 0, width, height],
                        "frame": current_frame,
                        "interpolate": True,
                        "keyframe": True,
                    },
                    {
                        "bounds": [0, 0, width, height],
                        "frame": end,
                        "interpolate": True,
                        "keyframe": True,
                    },
                ],
                "meta": {},
            }
            track_count += 1
            current_frame = endframe
        desfile = str(_working_directory_path / 'generatedAnnotations.json')
        with open(desfile, "w") as outfile:
            outfile.write(json.dumps({"tracks": tracks, "groups": {}, "version": 2}))
        # Now upload the new file to the folder and kick off a post process no job import.
        new_file = gc.uploadFileToFolder(folderId, desfile)
        # post process
        manager.updateStatus(JobStatus.PUSHING_OUTPUT)
        gc.addMetadataToItem(
            itemId,
            {
                "source_video": False,  # even though it is, this for requesting
                "transcoder": "ffmpeg",
                constants.OriginalFPSMarker: originalFps,
                constants.OriginalFPSStringMarker: avgFpsString,
                "codec": "h264",
            },
        )
        gc.addMetadataToFolder(
            folderId,
            {
                constants.DatasetMarker: True,  # mark the parent folder as able to annotate.
                constants.OriginalFPSMarker: originalFps,
                constants.OriginalFPSStringMarker: avgFpsString,
                constants.FPSMarker: originalFps,
                "ffprobe_info": videostream[0],
            },
        )
        gc.post(f'dive_rpc/postprocess/{folderId}', data={"skipJobs": True})
