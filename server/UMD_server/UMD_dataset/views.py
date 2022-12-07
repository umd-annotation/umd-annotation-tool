from dive_server import crud_annotation
from dive_utils import setContentDisposition
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.constants import AccessType, TokenScope
from girder.models.folder import Folder
from girder.models.token import Token
from girder.models.user import User
from girder_jobs.models.job import Job

from UMD_tasks import constants, tasks
from UMD_utils import UMD_export


class UMD_Dataset(Resource):
    def __init__(self):
        super(UMD_Dataset, self).__init__()
        self.resourceName = "UMD_dataset"

        self.route("POST", ("ingest_video", ":folderId"), self.ingest_video)
        self.route("GET", ("export", ":folderId"), self.export_tabular)

    @access.public(scope=TokenScope.DATA_READ, cookie=True)
    @autoDescribeRoute(
        Description("Export information in tablular form").modelParam(
            "folderId",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.WRITE,
            destName="folderId",
        )
    )
    def export_tabular(
        self,
        folderId,
    ):
        user = self.getCurrentUser()
        tracks = crud_annotation.TrackItem().list(folderId)
        users = list(User().find())
        userMap = {}
        for item in users:
            userMap[item["login"]] = item["_id"]

        fps = folderId['meta']['fps']
        gen = UMD_export.convert_to_zips(tracks, folderId, fps, userMap)
        zip_name = "batch_export.zip"
        setContentDisposition(zip_name, mime='application/zip')
        return gen

    @access.user
    @autoDescribeRoute(
        Description("Upload and generate a dataset from the folder").modelParam(
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
