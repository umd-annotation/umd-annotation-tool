import os

from dive_server import crud_annotation
from dive_utils import setContentDisposition
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource, getApiUrl
from girder.constants import AccessType, TokenScope
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.token import Token
from girder.models.user import User
from girder_jobs.models.job import Job
import requests

from UMD_tasks import constants, tasks
from UMD_utils import UMD_export


def mapUserIds(users):
    userMap = {}
    for item in users:
        uid = int(str(item["_id"]), 16)
        userMap[item["login"]] = {
            'id': str(item["_id"]),
            'login': item['login'],
            'email': item['email'],
            'first': item['firstName'],
            'last': item['lastName'],
            'uid': uid,
            'girderId': str(item["_id"])
        }
    return userMap


class UMD_Dataset(Resource):
    def __init__(self):
        super(UMD_Dataset, self).__init__()
        self.resourceName = "UMD_dataset"

        self.route("POST", ("ingest_video", ":folder"), self.ingest_video)
        self.route("POST", ("recursive_ingest_video", ":folder"), self.recursive_ingest_video)
        self.route("GET", ("export",), self.export_tabular)
        self.route("GET", ("recursive_export", ":folder"), self.export_resursive_tabular)
        self.route("GET", ("links", ":folder"), self.export_links)
        self.route("POST", ("update_containers",), self.update_containers)
        self.route("POST", ("mark_changepoint_complete",), self.mark_changepoint_complete)

    def recursive_folder_list(self, folder, totalFolders):
        subFolders = Folder().childFolders(folder, 'folder', user=self.getCurrentUser())
        subFolders = sorted(subFolders, key=lambda d: d['created'])
        for data in subFolders:
            if data['meta'].get('annotate', False) == True:
                totalFolders.append(data)
            else:
                self.recursive_folder_list(data, totalFolders)
        return totalFolders

    @access.public(scope=TokenScope.DATA_READ, cookie=True)
    @autoDescribeRoute(
        Description("Export link information for the root folder").modelParam(
            "folder",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.READ,
            destName="folder",
        )
    )
    def export_links(
        self,
        folder,
    ):
        totalFolders = []
        totalFolders = self.recursive_folder_list(folder, totalFolders)
        totalFolders = sorted(totalFolders, key=lambda d: d['created'])
        replacedHostname = getApiUrl().replace('/api/v1', '/#').replace('http', 'https')
        gen = UMD_export.generate_links_tab(replacedHostname, totalFolders)
        setContentDisposition('FolderLinks.csv', mime='text/csv')
        return gen

    @access.public(scope=TokenScope.DATA_READ, cookie=True)
    @autoDescribeRoute(
        Description("Export information in tablular form").jsonParam(
            "folderIds",
            "List of track types to filter by",
            paramType="query",
            required=True,
            default=[],
            requireArray=True,
        )
    )
    def export_tabular(
        self,
        folderIds,
    ):
        user = self.getCurrentUser()
        users = list(User().find())
        userMap = mapUserIds(users)

        gen = UMD_export.convert_to_zips(folderIds, userMap, user)
        if len(folderIds) > 1:
            zip_name = "batch_export.zip"
        else:
            folder = Folder().load(folderIds[0], level=AccessType.READ, user=user)
            zip_name = f'{folder["name"].replace(".mp4","")}.zip'
        setContentDisposition(zip_name, mime='application/zip')
        return gen

    @access.public(scope=TokenScope.DATA_READ, cookie=True)
    @autoDescribeRoute(
        Description("Export annotations for all the folders").modelParam(
            "folder",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.READ,
            destName="folder",
        )
    )
    def export_resursive_tabular(
        self,
        folder,
    ):
        totalFolders = []
        totalFolders = self.recursive_folder_list(folder, totalFolders)
        totalFolders = sorted(totalFolders, key=lambda d: d['created'])
        totalFolderIds = []
        for item in totalFolders:
            totalFolderIds.append(str(item['_id']))
        user = self.getCurrentUser()
        users = list(User().find())
        userMap = mapUserIds(users)

        gen = UMD_export.convert_to_zips(totalFolderIds, userMap, user)
        zip_name = "batch_export.zip"
        setContentDisposition(zip_name, mime='application/zip')
        return gen

    def generate_segment_task(self, folder, user):
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

    @access.user
    @autoDescribeRoute(
        Description("Upload and generate a dataset from the folder").modelParam(
            "folder",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.WRITE,
            destName="folder",
        )
    )
    def ingest_video(
        self,
        folder,
    ):
        user = self.getCurrentUser()
        self.generate_segment_task(folder, user)

    def generate_segments_of_children(self, folder, user):
        subFolders = list(Folder().childFolders(folder, 'folder', user))
        for child in subFolders:
            self.generate_segment_task(child, user)
            self.generate_segments_of_children(child, user)

    @access.user
    @autoDescribeRoute(
        Description(
            "Upload and generate a dataset from the folder and all it's children"
        ).modelParam(
            "folder",
            description="FolderId to get state from",
            model=Folder,
            level=AccessType.WRITE,
            destName="folder",
        )
    )
    def recursive_ingest_video(
        self,
        folder,
    ):
        user = self.getCurrentUser()
        self.generate_segments_of_children(folder, user)

    @access.admin
    @autoDescribeRoute(
        Description(
            "Force an update to the docker containers through watchtower using http interface"
        )
    )
    def update_containers(self):
        try:
            print('Sending Post Request')
            url = "http://watchtower:8080/v1/update"
            token = os.environ.get("WATCHTOWER_API_TOKEN", "mytoken")
            headers = {"Authorization": f"Bearer {token}"}
            req = requests.get(url, headers=headers)
            req.raise_for_status()
            return "Update Successful"
        except requests.exceptions.HTTPError as err:
            return f"HTTP error occurred: {err}"
        except requests.exceptions.ConnectionError as err:
            return f"Error Connecting: {err}"
        except requests.exceptions.Timeout as err:
            return f"Timeout Error: {err}"
        except requests.exceptions.RequestException as err:
            return f"Something went wrong: {err}"

    @access.admin
    @autoDescribeRoute(
        Description(
            "Force an update to the docker containers through watchtower using http interface"
        )
        .jsonParam(
            "data",
            description="Array of pairs of UserLogins and FolderIds",
            requireObject=True,
            paramType="body",
        )

    )
    def mark_changepoint_complete(self, data):
        # go through the list of data and fine the appropriate folder and user
        user = self.getCurrentUser()
        users = list(User().find())
        userMap = {}
        for item in users:
            userMap[item["login"]] = item["_id"]
        pairs = data['pairs']
        updated = []
        for pair in pairs:
            folderId = pair[1]
            userLogin = pair[0]
            print(f'UserLogin: {userLogin}')
            print(f'FolderId: {folderId}')
            if userLogin in userMap.keys():
                # now lets find the folder
                folder = Folder().load(folderId, level=AccessType.READ, user=user)
                tracks = crud_annotation.TrackItem().list(folder)
                last_track = tracks.limit(1).sort([('$natural', -1)])[0]
                attributes = last_track['attributes']
                attributes[f'{userLogin}_ChangePointComplete'] = True
                last_track['attributes'] = attributes
                upsert_tracks = [last_track]
                delete_tracks = [last_track['id']]
                crud_annotation.save_annotations(folder,
                                                 user,
                                                 upsert_tracks=upsert_tracks,
                                                 delete_tracks=delete_tracks,
                                                 upsert_groups=[],
                                                 delete_groups=[],
                                                 )
                updated.append(f'userId: {userLogin} and FolderId: {folderId} updated')
        return updated
