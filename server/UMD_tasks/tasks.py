from contextlib import suppress
import json
import os
import shutil
import subprocess
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile
from pathlib import Path
from subprocess import Popen
from sys import meta_path
from typing import Dict, List, Optional, Tuple
from urllib import request
from urllib.parse import urlparse
from PIL import Image
from UMD_tasks import constants, utils

from GPUtil import getGPUs
from girder_client import GirderClient
from girder_worker.app import app
from girder_worker.task import Task
from girder_worker.utils import JobManager, JobStatus

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
def empty_task(self: Task,):
    gc: GirderClient = self.girder_client
    manager: JobManager = self.job_manager
    print('Empty Task')

