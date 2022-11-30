import math
from girder import logger
from girder.api import access
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


class UMD_Dataset(Resource):
    def __init__(self):
        super(UMD_Dataset, self).__init__()
        self.resourceName = "UMD_dataset"

        self.route("GET", ("temp",), self.temp_endpoint)

    @access.user
    @autoDescribeRoute(
        Description("Temporary endpoint for the plugin")
        .pagingParams("created")
    )
    def temp_endpoint(self, params):
        return True
