from girder import plugin
from .client_webroot import ClientWebroot
from .UMD_dataset.views import UMD_Dataset

class UMDPlugin(plugin.GirderPlugin):
    def load(self, info):
        info["apiRoot"].UMD_dataset = UMD_Dataset()
        # nothing yet
