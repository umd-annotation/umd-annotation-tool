import girder_client
import json
import click
import requests



JSONLSourceFolderId = ""
VideoSourceFolderId = "6602d4a4cb9585b0c24b794f"
CloneDestinationFolderId = ""

apiURL = "annotation.umd.edu"

def login():
    gc = girder_client.GirderClient(apiURL, port=443, apiRoot='girder/api/v1' )
    with gc.session() as session:
        session.verify = False
        gc.authenticate(interactive=True)
        return gc


def getFolderList(gc: girder_client.GirderClient, folderId, parentType = "folder"):
    folders = list(gc.listFolder(folderId, parentFolderType=parentType))
    print(folders)
    return folders

def get_processVideos(gc, folderId):
    videoList = getFolderList(VideoSourceFolderId)
    video_dict = {}
    for item in videoList:
        if "THIRD-PERSON.mp4" in item.name and 'annotate' in item.meta.keys():
            updated_name = item.name.replace("Video ", "").replace("THIRD-PERSON.mp4", "")
            video_dict[updated_name] = item.id

    print(video_dict)
    return video_dict



@click.command(name="removeDups", help="Load in ")
def run_script():
    gc = login()
    VideoList = getFolderList(gc, VideoSourceFolderId)





if __name__ == '__main__':
    run_script()
