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

BASENORMMAP = [
    {"named": 'No Norm', "id": 100, "groups": ['LC1', 'LC2', 'LC3', 'LC4']},
    {"named": 'Apology', "id": 101, "groups": ['LC1', 'LC2', 'LC3', 'LC4']},
    {"named": 'Criticism', "id": 102, "groups": ['LC1', 'LC2']},
    {"named": 'Greeting', "id": 103, "groups": ['LC1', 'LC2', 'LC3', 'LC4']},
    {"named": 'Request', "id": 104, "groups": ['LC1']},
    {"named": 'Persuasion', "id": 105, "groups": ['LC1']},
    {"named": 'Thanks', "id": 106, "groups": ['LC1', 'LC2', 'LC3', 'LC4']},
    {"named": 'Taking Leave', "id": 107, "groups": ['LC1']},
    {"named": 'Admiration', "id": 108, "groups": ['LC1', 'LC2', 'LC3']},
    {"named": 'Finalizing Negotiation/Deal', "id": 109, "groups": ['LC1', 'LC2']},
    {"named": 'Refusing a Request', "id": 110, "groups": ['LC1', 'LC2']},
    {"named": 'Requesting Information', "id": 111, "groups": ['LC2', 'LC3']},
    {"named": 'Granting a Request', "id": 112, "groups": ['LC2', 'LC3', 'LC4']},
    {"named": 'Disagreement', "id": 113, "groups": ['LC2', 'LC3']},
    {"named": 'Respond to Request for Information', "id": 114, "groups": ['LC3', 'LC4']},
    {"named": 'Acknowledging Thanks', "id": 115, "groups": ['LC3', 'LC4']},
    {"named": 'Interrupting', "id": 116, "groups": ['LC3', 'LC4']},
    {"named": 'Complaining', "id": 117, "groups": ['LC4']},
    {"named": 'Topic Closing', "id": 118, "groups": ['LC4']},
    {"named": 'Giving Advice', "id": 119, "groups": ['LC4']},
]


class TA2NormMapping(BaseModel):
    named: str
    id: int
    groups: List[str]


class TA2Config(BaseModel):
    normMap: List[TA2NormMapping]

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
        return Setting().get(TA2_CONFIG) or {'normMap': BASENORMMAP}

    @access.admin
    @autoDescribeRoute(
        Description("update TA2 Config").jsonParam(
            "data", "Update TA2 Config", paramType='body', requireObject=True, required=True
        )
    )
    def update_ta2_config(self, data):
        Setting().set(TA2_CONFIG, data)
