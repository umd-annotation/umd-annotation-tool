from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import Resource
from girder.models.setting import Setting
from girder.exceptions import RestException, ValidationException
from girder.utility import setting_utilities
from pydantic.main import BaseModel
import pydantic
from typing import Any, Dict, List, Optional, Tuple, Union

TA2_CONFIG = 'TA2_config'

class TA2NormMapping(BaseModel):
    name: str
    id: int
    groups: List[str]

class TA2Config(BaseModel):
    normMapping: List[TA2NormMapping]

    class Config:
        extra = 'forbid'



def get_validated_model(model: BaseModel, **kwargs):
    try:
        return model(**kwargs)
    except pydantic.ValidationError as err:
        raise ValidationException(err)


@setting_utilities.validator({TA2_CONFIG})
def validateTranscodeConfig(doc):
    val = doc['value']
    if val is not None:
        get_validated_model(TA2Config, **val)


class ConfigurationResource(Resource):
    """Configuration resource handles get/set of global configuration"""

    def __init__(self, resourceName):
        super(ConfigurationResource, self).__init__()
        self.resourceName = resourceName

        self.route("GET", ("TA2_config",), self.get_ta2_config)
        self.route("PUT", ("TA2_config",), self.update_ta2_config)

    @access.public
    @autoDescribeRoute(Description("Get TA2 Config"))
    def get_ta2_config(self):
        return Setting().get(TA2_CONFIG) or {}

    @access.admin
    @autoDescribeRoute(
        Description("update TA2 Config").jsonParam(
            "data", "Update TA2 Config", paramType='body', requireObject=True, required=True
        )
    )
    def update_ta2_config(self, data):
        Setting().set(TA2_CONFIG, data)