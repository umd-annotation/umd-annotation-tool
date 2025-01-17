from girder import plugin, events

from .UMD_dataset.views import UMD_Dataset
from .client_webroot import ClientWebroot
from .UMD_dataset.event import process_s3_import
from .UMD_configuration.views import ConfigurationResource
class UMDPlugin(plugin.GirderPlugin):
    def load(self, info):
        info["apiRoot"].UMD_dataset = UMD_Dataset()
        info["apiRoot"].UMD_configuration = ConfigurationResource("UMD_configuration")

        events.bind(
            "s3_assetstore_imported",
            "process_s3_import",
            process_s3_import,
        )
