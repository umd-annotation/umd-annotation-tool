from datetime import datetime, timedelta
from pathlib import Path
import re
import shutil
import signal
import subprocess
from subprocess import Popen
import tempfile
from tempfile import mktemp
from typing import IO, Any, Callable, Dict, List, Optional, Union

from girder_client import GirderClient
from girder_worker.task import Task
from girder_worker.utils import JobManager, JobStatus

TIMEOUT_COUNT = 'timeout_count'
TIMEOUT_LAST_CHECKED = 'last_checked'
TIMEOUT_CHECK_INTERVAL = 30


class CanceledError(RuntimeError):
    pass


def check_canceled(task: Task, context: dict, force=True):
    """
    Only check for canceled task every interval unless force is true (default).
    This is an expensive operation that round-trips to the message broker.
    """
    if not context.get(TIMEOUT_COUNT):
        context[TIMEOUT_COUNT] = 0
    now = datetime.now()
    if (
        (now - context.get(TIMEOUT_LAST_CHECKED, now)) > timedelta(seconds=TIMEOUT_CHECK_INTERVAL)
    ) or force:
        context[TIMEOUT_LAST_CHECKED] = now
        try:
            return task.canceled
        except (TimeoutError, ConnectionError) as err:
            context[TIMEOUT_COUNT] += 1
            print(
                f"Timeout N={context[TIMEOUT_COUNT]} for this task when checking for "
                f"cancellation. {err}"
            )
    return False


def stream_subprocess(
    task: Task,
    context: dict,
    manager: JobManager,
    popen_kwargs: dict,
    keep_stdout: bool = False,
) -> str:
    """
    Stream live results from process to job manager

    :param task: task to detect cancelation
    :param manager: job manager
    :param popen_kwargs: a dict to pass as kwargs to popen.  Must include 'args'
    :param keep_stdout: will return stdout as a string if needed
    """
    start_time = datetime.now()
    stdout = ""
    assert 'args' in popen_kwargs, "popen_kwargs must contain key 'args'"

    with tempfile.TemporaryFile() as stderr_file:
        manager.write(f"Running command: {str(popen_kwargs['args'])}\n", forceFlush=True)
        process = Popen(
            **popen_kwargs,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
        )

        if process.stdout is None:
            raise RuntimeError("Stdout must not be none")

        # call readline until it returns empty bytes
        for line in iter(process.stdout.readline, b''):
            line_str = line.decode('utf-8')
            manager.write(line_str)
            if keep_stdout:
                stdout += line_str

            if check_canceled(task, context, force=False):
                # Can never be sure what signal a process will respond to.
                process.send_signal(signal.SIGTERM)
                process.send_signal(signal.SIGKILL)

        # flush logs
        manager._flush()
        # Wait for exit up to 30 seconds after kill
        code = process.wait(30)

        if check_canceled(task, context):
            manager.write('\nCanceled during subprocess run.\n')
            manager.updateStatus(JobStatus.CANCELED)
            raise CanceledError('Job was canceled')

        if code > 0:
            stderr_file.seek(0)
            stderr = stderr_file.read().decode()
            raise RuntimeError(
                'Pipeline exited with nonzero status code {}: {}'.format(process.returncode, stderr)
            )
        else:
            end_time = datetime.now()
            manager.write(f"\nProcess completed in {str((end_time - start_time))}\n")

        return stdout


def get_video_filename(folderId: str, girder_client: GirderClient) -> Optional[str]:
    """
    Searches a folderId for videos that are compatible with training/pipelines

    * look for {"codec": 'h264', "source_video": False | None }, a transcoded video
    * then fall back to {"source_video": True}, the user uploaded video
    * If neither found it will return None

    :folderId: Current path to where the items sit
    :girder_client: girder_client used to request the data
    """
    folder_contents = girder_client.listItem(folderId)
    backup_converted_file = None
    for item in folder_contents:
        file_name = item.get("name")
        meta = item.get("meta", {})
        if meta.get("source_video") is True:
            backup_converted_file = file_name
        elif meta.get("codec") == "h264":
            return file_name
    return backup_converted_file


def fromMeta(obj, key: str, default=None, required=False) -> Any:
    """Safely get a property from girder metadata"""
    if not required:
        return obj.get("meta", {}).get(key, default)
    else:
        return obj["meta"][key]


def download_source_media(girder_client: GirderClient, folder, dest: Path) -> List[str]:
    """
    Download source media for folder from girder
    """
    if fromMeta(folder, 'type') == 'image-sequence':
        image_items = girder_client.get('meva/valid_images', {'folderId': folder["_id"]})
        for item in image_items:
            girder_client.downloadItem(str(item["_id"]), str(dest))
        return [str(dest / item['name']) for item in image_items]
    elif fromMeta(folder, 'type') == 'video':
        clip_meta = girder_client.get("meva_detection/clip_meta", {'folderId': folder['_id']})
        destination_path = str(dest / clip_meta['video']['name'])
        girder_client.downloadFile(str(clip_meta['video']['_id']), destination_path)
        return [destination_path]
    else:
        raise Exception(f"unexpected folder {str(folder)}")
