from datetime import datetime, timedelta
import os

from bson.objectid import ObjectId
from girder import logger
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.file import File
from girder.models.assetstore import Assetstore
from girder.models.setting import Setting
from girder.models.user import User
from girder.settings import SettingKey
from girder.utility.mail_utils import renderTemplate, sendMail
from girder.models.token import Token
from UMD_tasks import constants, tasks
from girder_jobs.models.job import Job
from dive_server import crud_annotation

from dive_utils import asbool, fromMeta
from dive_utils.constants import (
    AssetstoreSourceMarker,
    AssetstoreSourcePathMarker,
    DatasetMarker,
    DefaultVideoFPS,
    FPSMarker,
    ImageSequenceType,
    TypeMarker,
    VideoType,
    imageRegex,
    videoRegex,
)

def generate_segment_task(folder, user):
        token = Token().createToken(user=user, days=2)
        videoItems = Folder().childItems(
            folder, user=user, filters={"lowerName": {"$regex": constants.videoRegex}}
        )
        folder['meta']['type'] = 'video'
        Folder().save(folder)
        tracks = crud_annotation.TrackItem().list(folder)

        if len(list(tracks)) == 0:
            for item in videoItems:
                newjob = tasks.generate_splits.delay(
                    folderId=str(item["folderId"]),
                    itemId=str(item["_id"]),
                    user_id=str(user["_id"]),
                    user_login=str(user["login"]),
                    girder_job_title="Generating Tracks for UMD video",
                    girder_client_token=str(token["_id"]),
                )
                Job().save(newjob.job)
        else: 
            originalFPS = folder['meta'][constants.OriginalFPSMarker]
            originalFPSString = folder['meta'][constants.OriginalFPSStringMarker]
            for item in videoItems:
                if item['meta'].get('source_video', None) is None:
                    data = {
                        'source_video': False,
                        'transcoder': 'ffmpeg',
                        'originalFps': originalFPS,
                        'originalFpsString': originalFPSString,
                        'codec': 'h264'
                    }
                    item['meta'].update(data)
                    Item().save(item)

def process_assetstore_import(event, meta: dict):
    """
    Function for appending the appropriate metadata to no-copy import data
    """
    info = event.info
    objectType = info.get("type")
    importPath = info.get("importPath")
    now = datetime.now()

    if not importPath or not objectType or objectType != "item":
        return
    
    dataset_type = None
    item = Item().findOne({"_id": info["id"]})
    item['meta'].update(
        {
            **meta,
            AssetstoreSourcePathMarker: importPath,
        }
    )
    if imageRegex.search(importPath):
        dataset_type = ImageSequenceType

    elif videoRegex.search(importPath):
        # Look for exisitng video dataset directory
        parentFolder = Folder().findOne({"_id": item["folderId"]})
        userId = parentFolder['creatorId'] or parentFolder['baseParentId']
        user = User().findOne({'_id': ObjectId(userId)})
        foldername = f'Video {item["name"]}'
        dest = Folder().createFolder(parentFolder, foldername, creator=user, reuseExisting=True)
        if dest['created'] < now:
            # Remove the old item, replace it with the new one.
            oldItem = Item().findOne({'folderId': dest['_id'], 'name': item['name']})
            if oldItem is not None:
                Item().remove(oldItem)
        Item().move(item, dest)
        dataset_type = VideoType

    if dataset_type is not None:
        # Update metadata of parent folder
        # FPS is hardcoded for now
        Item().save(item)
        folder = Folder().findOne({"_id": item["folderId"]})
        root, _ = os.path.split(importPath)
        if not asbool(fromMeta(folder, DatasetMarker)):
            folder["meta"].update(
                {
                    TypeMarker: dataset_type,
                    FPSMarker: DefaultVideoFPS,
                    DatasetMarker: True,
                    AssetstoreSourcePathMarker: root,
                    **meta,
                }
            )
            Folder().save(folder)
        generate_segment_task(folder, user)
    return


def process_s3_import(event):
    return process_assetstore_import(event, {AssetstoreSourceMarker: 's3'})