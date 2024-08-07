import girder_client
import json
import click
import requests
import csv
import os
from fuzzywuzzy import process


ADD_CLNG_VIDEOS = True # will add the CLNG labelled videos with TURN creation links
JSONLSourceFolderId = "6627ef547193244a6e33353d" # the GirderId of the folder that contains the source JSONL files
VideoSourceFolderIds = ["6602d4a4cb9585b0c24b794f", "65e72cd2cb9585b0c24b3ac1"] # folders to search for matching Video files
CloneDestinationFolderId = "663a51a00e61a67154749750" # destination girder folder ID for the cloned videos

apiURL = "annotation.umd.edu"

processingDirectory = './jsonProcessing'
tracksDirectory = './tracks'



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
            if "THIRD-PERSON.mp4" in item["name"] and 'annotate' in item["meta"].keys():
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


def get_processJSONItems(gc: girder_client.GirderClient, folderId):
    items = list(getItemList(gc, folderId))
    item_dict = {}
    for item in items:
        update_name = item["name"].replace('_converted.json', '').replace('log_', '')
        item_dict[update_name] = item["_id"]
    return item_dict

def find_top_matches(input_string, listB):
    matches = process.extract(input_string, listB, limit=5)
    return matches


@click.command(name="cloneAndConvert", help="Load in ")
def run_script():
    gc = login()
    video_map = get_processVideos(gc)
    print(video_map)


if __name__ == '__main__':
    run_script()


