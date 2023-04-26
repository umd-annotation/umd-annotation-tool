import os
import click
import json
import math
import csv
from collections import OrderedDict

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
    "none": "None",
}

normValMap = {
    'adhere': 'adhered',
    'violate': 'violated',
    'EMPTY_NA': 'EMPTY_NA',
    'adhere_violate': 'adhered_violated'
}



def loadUserMap(csvfile):
    userMap = {}
    with open(csvfile, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter='\t')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            userMap[row['uid']] = row['login']
            line_count += 1
        print(f'Processed {line_count} lines.')
    print(userMap)
    return userMap

def loadExistingTracks(trackFile):
    with open(trackFile, 'r') as myfile:
        file_data = myfile.read()
        data = json.loads(file_data)
        tracks = data['tracks']
        return tracks

def loadValenceArousal(tabFile, videoname, userMap):
    annotations = {}
    with open(tabFile, mode='r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter='\t')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            if row['file_id'].lower() in videoname:
                segmentstr = row['segment_id'].replace(f"{row['file_id']}_", '')
                segment = float(segmentstr)
                if segment not in annotations:
                    annotations[segment] = {}
                login = userMap[row['user_id']]
                valence = int(row['valence_continuous'])
                arousal = int(row['arousal_continuous'])
                if login not in annotations[segment]:
                    annotations[segment][login] = { 'valence': valence, 'arousal': arousal }
            line_count += 1
    return annotations

def loadEmotions(tabFile, videoname, userMap):
    annotations = {}
    with open(tabFile, mode='r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter='\t')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            if row['file_id'].lower() in videoname:
                segmentstr = row['segment_id'].replace(f"{row['file_id']}_", '')
                segment = float(segmentstr)
                if segment not in annotations:
                    annotations[segment] = {}
                login = userMap[row['user_id']]
                emotions = (row['emotion'])
                emotionList = emotions.split(',')
                upperList = []
                for emotion in emotionList:
                    upperList.append(emotion.capitalize())
                joined = '_'.join(upperList)
                multispeaker = (row['multi_speaker'])
                if joined == 'None':
                    joined = 'No emotions'
                    multispeaker = 'FALSE'
                if login not in annotations[segment]:
                    annotations[segment][login] = { 'emotions': joined, 'multispeaker': multispeaker }
            line_count += 1
    return annotations

def loadNorms(tabFile, videoname, userMap):
    annotations = {}
    with open(tabFile, mode='r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter='\t')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            if row['file_id'].lower() in videoname:
                segmentstr = row['segment_id'].replace(f"{row['file_id']}_", '')
                segment = float(segmentstr)
                if segment not in annotations:
                    annotations[segment] = {}
                login = userMap[row['user_id']]
                norm = normMap[(row['norm'])]
                status = normValMap[row['status']]
                if login not in annotations[segment]:
                    annotations[segment][login] = { }                
                annotations[segment][login][norm] = status
            line_count += 1
    return annotations

def loadChangePoints(tabFile, videoname, userMap):
    annotations = {}
    with open(tabFile, mode='r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter='\t', quotechar='"')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            if row['file_id'].lower() in videoname:
                timestamp = float(row['timestamp'])
                impact_scalar = int(row['impact_scalar']) * 1000 # 1 to 5000 value needs to be remapped
                comment = row['comment']
                login = row['user_id']
                frame = round(timestamp * 30.0)
                if frame not in annotations:
                    annotations[frame] = {}
                if login not in annotations[frame]:
                    annotations[frame][login] = { }                
                annotations[frame][login]= {
                    'comment': comment,
                    'impact': impact_scalar,

                }
            line_count += 1
    return annotations


def generate_tracks(videoinfo):
    # skip first 5 seconds
    fps = videoinfo["frames_per_sec"]
    width = videoinfo["width"]
    height = videoinfo["height"]
    start = fps * 5.0
    framecount = videoinfo["framecount"]
    current_frame = start
    tracks = {}
    track_count = 0
    while current_frame < framecount:
        end = min(framecount, current_frame + (15.0 * fps))
        tracks[track_count] = {
            "begin": int(current_frame),
            "end": int(end),
            "id": track_count,
            "confidencePairs": [["segment", 1.0]],
            "attributes": {},
            "meta": {},
            "features": [
                {
                    "frame": int(current_frame),
                    "bounds": [0, 0, width, height],
                    "interpolate": True,
                    "keyframe": True,
                },
                {
                    "frame": int(end),
                    "bounds": [0, 0, width, height],
                    "interpolate": True,
                    "keyframe": True,
                },
            ],
        }
        track_count += 1
        current_frame = current_frame + (15.0 * fps)
    return tracks


@click.command(
    name="Convert a Tab Folder to track.JSON file",
    help="Takes a video and meta config and generates a track file",
)
@click.argument("trackfile")
def load_data(trackfile):
   #tracks = loadExistingTracks(trackfile)
    videoinfo = {
        'width': 1920,
        'height': 1080,
        'frames_per_sec': 30.0,
        'framecount': 26712
    }
    tracks = generate_tracks(videoinfo)
    userMap = loadUserMap('./userMap.tab')
    valence_annotations = loadValenceArousal('./valence_arousal.tab', trackfile, userMap)
    norms_annotations = loadNorms('./norms.tab', trackfile, userMap)
    emotion_annotations = loadEmotions('./emotions.tab', trackfile, userMap)
    changepoints = loadChangePoints('./changepoint.tab', trackfile, userMap)
    # So now we need to update the TrackJSON for all of these annotations
    for trackId in tracks.keys():
        track = tracks[trackId]
        if trackId in valence_annotations:
            valence_segment = valence_annotations[trackId]
            for user in valence_segment.keys():
                track['attributes'][f'{user}_Valence'] = valence_segment[user]['valence']
                track['attributes'][f'{user}_Arousal'] = valence_segment[user]['arousal']
        if trackId in emotion_annotations:
            emotion_segment = emotion_annotations[trackId]
            for user in emotion_segment.keys():
                track['attributes'][f'{user}_Emotions'] = emotion_segment[user]['emotions']
                track['attributes'][f'{user}_MultiSpeaker'] = emotion_segment[user]['multispeaker']
        if trackId in norms_annotations:
            norms_segment = norms_annotations[trackId]
            for user in norms_segment.keys():
                track['attributes'][f'{user}_Norms'] = norms_segment[user]
    # changepoints are slightly different they require finding the segment and injecting the track feature are the proper frame
    for frame in changepoints.keys():
        segment = (math.floor(((frame - 150) / 450)))
        print(segment)
        for user in changepoints[frame].keys():
            comment = changepoints[frame][user]['comment']
            impact = changepoints[frame][user]['impact']
            tracks[segment]['features'].append({
                "frame": frame,
                "bounds": [0, 0, 1920, 1080],
                "attributes": {
                    f"{user}_Comment": comment,
                    f"{user}_ImpactV2.0": impact
                },
                "interpolate": True,
                "keyframe": True
            })
        tracks[segment]['features'] = sorted(tracks[segment]['features'], key=lambda d: d['frame'])
        tracks[segment]['attributes'] = OrderedDict(sorted(tracks[segment]['attributes'].items()))

    with open(trackfile.replace('.json', '.output.json'), "w") as outfile:
        outfile.write(json.dumps({"tracks": tracks, "groups": {}, "version": 2}))


if __name__ == "__main__":
    load_data()
