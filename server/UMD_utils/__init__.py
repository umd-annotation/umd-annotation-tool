from typing import Any, Dict, List, Optional, Tuple

from girder.utility import ziputil

from UMD_utils import UMD_export, types

TRUTHY_META_VALUES = ['yes', '1', 1, 'true', 't', 'True', True]
FALSY_META_VALUES = ['no', '0', 0, 'false', 'f', 'False', False]
