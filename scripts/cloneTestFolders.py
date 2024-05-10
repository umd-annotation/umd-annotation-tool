import girder_client
import json
import click
import requests
import csv
import os
from fuzzywuzzy import process


ADD_CLNG_VIDEOS = True # will add the CLNG labelled videos with TURN creation links
VideoSourceFolderIds = ["66291d1f7fc0ad6d09f3596a"] # folders to search for matching Video files
CloneDestinationFolderId = "663a5f090e61a6715474cb59" # destination girder folder ID for the cloned videos

apiURL = "annotation.umd.edu"

processingDirectory = './jsonProcessing'
tracksDirectory = './tracks'

normMap = {
    '101': "Apology",
    '102': "Criticism",
    '103': "Greeting",
    '104': "Request",
    '105': "Persuasion",
    '106': "Thanks",
    '107': "Taking Leave",
    '108': "Admiration",
    '109': "Finalizing Negotiation/Deal",
    '110': "Refusing a Request",
    '111': "Requesting Information",
    '112': "Granting a Request",
    '113': "Disagreement",
    '114': "Respond to Request for Information",
    '115': "Acknowledging Thanks",
    '116': "Interrupting",
    "none": "None",
}


def login():
    gc = girder_client.GirderClient(apiURL, port=443, apiRoot='girder/api/v1' )
    gc.authenticate(interactive=True)
    return gc


def getFolderList(gc: girder_client.GirderClient, folderId, parentType = "folder"):
    folders = list(gc.listFolder(folderId, parentFolderType=parentType))
    return folders

def getItemList(gc: girder_client.GirderClient, folderId):
    items = list(gc.listItem(folderId))
    return items

def get_processVideos(gc):
    video_dict = {}
    for VideoSourceFolderId in VideoSourceFolderIds:
        videoList = getFolderList(gc, VideoSourceFolderId)
        for item in videoList:
            if 'annotate' in item["meta"].keys():
                updated_name = item["name"].replace("Video ", "").replace("_THIRD-PERSON.mp4", "")
                video_dict[updated_name] = item["_id"]
    return video_dict

def get_existingVideos(gc, folderId):
    videoList = getFolderList(gc, folderId)
    video_dict = {}
    for item in videoList:
        if 'annotate' in item["meta"].keys():
            updated_name = item["name"].replace("Video ", "").replace("_THIRD-PERSON.mp4", "")
            video_dict[updated_name] = item["_id"]

    return video_dict





def clone_video_folder(gc: girder_client.GirderClient, datasetId, name, destId):
    clonedFolder = gc.sendRestRequest('POST', f'dive_dataset?cloneId={datasetId}&parentFolderId={destId}&name={name}_CLNG')
    return clonedFolder["_id"]

def upload_track_json(gc: girder_client.GirderClient, destFolderId, trackJsonFile):
    gc.uploadFileToFolder(destFolderId, trackJsonFile)
    gc.sendRestRequest('POST', f'dive_rpc/postprocess/{destFolderId}', data={'skipTranscoding': True, 'skipJobs': True})
    gc.addMetadataToFolder(destFolderId, {"UMDAnnotation": "TA2"})

@click.command(name="cloneAndConvert", help="Load in ")
def run_script():
    gc = login()
    clng_videos = get_processVideos(gc)
    # write the unmatched items to unmatching.json

    count = 0
    limit = 9999
    completed_videos = []
    for key in clng_videos.keys():

        for key in clng_videos.keys():
            item = clng_videos[key]
            cloneId = clone_video_folder(gc, item, key, CloneDestinationFolderId)
            gc.addMetadataToFolder(cloneId, {"UMDAnnotation": "TA2"})
            trackJSON = {"tracks": {}, "groups": {}, "version": 2}
            with open('emptyTracks.json', 'w', encoding='utf8') as outfile:
                json.dump(trackJSON, outfile, ensure_ascii=False, indent=True)
            gc.uploadFileToFolder(cloneId, 'emptyTracks.json')
            gc.sendRestRequest('POST', f'dive_rpc/postprocess/{cloneId}', data={'skipTranscoding': True, 'skipJobs': True})
            completed_videos.append({'name': key, 'id': cloneId, 'CLNG': True})



if __name__ == '__main__':
    run_script()


