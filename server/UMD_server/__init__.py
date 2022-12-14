from girder import plugin

from .UMD_dataset.views import UMD_Dataset
from .client_webroot import ClientWebroot


class UMDPlugin(plugin.GirderPlugin):
    def load(self, info):
        info["apiRoot"].UMD_dataset = UMD_Dataset()
        # nothing yet
