import math
from girder import logger
from girder.api import access
from girder.constants import AccessType
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.constants import SortDir
from girder.exceptions import RestException
from girder.models.assetstore import Assetstore
from girder.models.folder import Folder
from girder.models.user import User
from girder.models.file import File
from girder.models.item import Item
from girder.models.token import Token
from UMD_tasks import constants, tasks
from girder.models.token import Token
from girder_jobs.models.job import Job


class UMD_Dataset(Resource):
    def __init__(self):
        super(UMD_Dataset, self).__init__()
        self.resourceName = "UMD_dataset"

        self.route("GET", ("temp",), self.temp_endpoint)
        self.route("POST", ("ingest_video", ":folderId"), self.ingest_video)

    @access.user
    @autoDescribeRoute(
        Description("Temporary endpoint for the plugin")
        .pagingParams("created")
    )
    def temp_endpoint(self, params):
        return True


    @access.user
    @autoDescribeRoute(
        Description("Upload and generate a dataset from the folder")
        .modelParam(
            "folderId",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.WRITE,
            destName="folderId",
        )
    )
    def ingest_video(
        self,
        folderId,
    ):
        user = self.getCurrentUser()
        token = Token().createToken(user=user, days=2)
        videoItems = Folder().childItems(
            folderId, filters={"lowerName": {"$regex": constants.videoRegex}}
        )
        folderId['meta'] = {'type': 'video'}
        Folder().save(folderId)

        for item in videoItems:
            newjob = tasks.generate_splits.delay(
                folderId=str(item["folderId"]),
                itemId=str(item["_id"]),
                user_id=str(user["_id"]),
                user_login=str(user["login"]),
                girder_job_title=f"Generating Tracks for UMD video",
                girder_client_token=str(token["_id"]),
            )
            Job().save(newjob.job)