import girder_client
import json
import click
import requests
import os
from fuzzywuzzy import process

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

JSONLSourceFolderId = "6627ef547193244a6e33353d"
VideoSourceFolderIds = ["6602d4a4cb9585b0c24b794f", "65e72cd2cb9585b0c24b3ac1"]
CloneDestinationFolderId = "661e8fceaee0d357e2455d47"

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


def get_matching_items(video_dict, item_dict):
    matching = {}
    unmatching = []
    for key in item_dict.keys():
        if video_dict.get(key, False):
            matching[key] = {"videoId": video_dict[key], "jsonId": item_dict[key]}
        else:
            top_matches = find_top_matches(key, video_dict.keys())
            potentials = []
            matched = False
            for item in top_matches:
                if item[1] >= 95 and not matched:
                    matched = True
                    matching[key] = {"videoId": video_dict.get(item[0]), "jsonId": item_dict[key],}
                potentials.append({'videoName': item[0], 'percentMatch': item[1], "videoId": video_dict.get(item[0], False)})
            unmatching.append({"unmatchedJSONName": key, "unmatchedJSONId": item_dict[key], "potentialVideoMatches": potentials, "foundMatch": matched})

    return matching, unmatching

def download_and_process_json(gc: girder_client.GirderClient, itemId, name):
    if not os.path.exists(processingDirectory):
        os.mkdir(processingDirectory)
    gc.downloadItem(itemId, processingDirectory)
    # next we need to process the downloaded file and convert it into a track json
    try: 
        with open(f"{processingDirectory}/log_{name.replace('.json', '_converted.json')}", 'r', encoding='utf8') as f:
            turns_output = json.load(f)
    except:
        with open(f"{processingDirectory}/log_{name.replace('.json', '_converted.json')}", 'r', encoding='latin-1') as f:
            turns_output = json.load(f)

    turns = process_outputjson(turns_output)
    trackJSON = convert_output_to_tracks(turns)
    if not os.path.exists(tracksDirectory):
        os.mkdir(tracksDirectory)
    trackJSONFilePath = os.path.join(tracksDirectory, name)
    with open(trackJSONFilePath, 'w', encoding='utf8') as outfile:
        json.dump(trackJSON, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')
    return trackJSONFilePath

def clone_video_folder(gc: girder_client.GirderClient, datasetId, name, destId):
    clonedFolder = gc.sendRestRequest('POST', f'dive_dataset?cloneId={datasetId}&parentFolderId={destId}&name={name}')
    return clonedFolder["_id"]

def upload_track_json(gc: girder_client.GirderClient, destFolderId, trackJsonFile):
    gc.uploadFileToFolder(destFolderId, trackJsonFile)
    gc.sendRestRequest('POST', f'dive_rpc/postprocess/{destFolderId}', data={'skipTranscoding': True, 'skipJobs': True})
    gc.addMetadataToFolder(destFolderId, {"UMDAnnotation": "TA2"})


@click.command(name="removeDups", help="Load in ")
def run_script():
    gc = login()
    video_map = get_processVideos(gc)
    existing_videos = get_existingVideos(gc, CloneDestinationFolderId)
    item_map = get_processJSONItems(gc, JSONLSourceFolderId)
    matching, unmatching = get_matching_items(video_map, item_map)
    # write the unmatched items to unmatching.json
    with open('unmatching.json', 'w', encoding='utf8') as outfile:
        json.dump(unmatching, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')

    count = 0
    limit = 9999
    print(existing_videos)
    for key in matching.keys():
        if key in existing_videos.keys():
            print(f'Skipping video: {key} it already exists')
            continue
        item = matching[key]
        trackJSONFilePath = download_and_process_json(gc, item["jsonId"], f"{key}.json")
        item["trackJSON"] = trackJSONFilePath
        cloneId = clone_video_folder(gc, item["videoId"], key, CloneDestinationFolderId)
        item["cloneId"] = cloneId
        upload_track_json(gc, cloneId, trackJSONFilePath)
        count += 1
        if count > limit:
            break


    





def create_or_get_turn(turns, start_time, end_time, time_seconds):
    
    for item in turns:
        if item['startTime'] == start_time and item['endTime'] == end_time:
            item['startglobal'] = min(time_seconds, item['startglobal'])
            item['endglobal'] = max(time_seconds, item['endglobal'])
            return item
    turn = {
        'startTime': start_time,
        'endTime': end_time,
        'startglobal':time_seconds,
        'endglobal': time_seconds,
    }
    turns.append(turn)
    return turn


def process_outputjson(output):
    turns = []
    print('processing output file')
    translations = []
    ptt_turns = []
    for item in output:
        if item.get('queue', False) == 'AUDIO_SELF' and item.get('message', {}).get('status', False) in ['ptt-pressed', 'ptt-released']:
            ptt_turns.append({
                "status": item.get('message', {}).get('status', False),
                "seconds": item.get('time_seconds')
            })
        # we have a turn with ASR information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'asr_result':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['ASRText'] = item['message']['asr_text']
            turn['speaker'] = item['message']['speaker']
        # translation information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'translation':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['translation'] = {
                'source_language': item['message']['source_language'],
                'target_language': item['message']['target_language'],
                'speaker': item['message']['speaker'],
                'text': item['message']['translation'],
            }
        # translation of possible Rephrasing
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TEXT' and item.get('message', {}).get('type', False) == 'translation':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            if turn.get('rephrase_translation', None) is None:
                turn['rephrase_translation'] = []
            turn['rephrase_translation'].append({
                'source_language': item['message']['source_language'],
                'target_language': item['message']['target_language'],
                'speaker': item['message']['speaker'],
                'text': item['message']['translation'],
                'sourceText': item['message']['text'],
            })
        # storing emotions for future use
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'sri_emotions':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['emotions'] = item['message']['emotions']
        # intent and rudeness
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'intent_and_rudeness':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['intent_and_rudeness'] = {
                "class1": item['message']['class1'],
                "class_probability1": item['message']['class_probability1'],
                "class2": item['message']['class2'],
                "class_probability2": item['message']['class_probability2'],
                "rudeness_detected": item['message']['rudeness_detected'],
                "rudeness_detected_score": item['message']['rudeness_detected_score'],
            }
        # paraphrasing results
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'paraphrase_result':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            paraphrase = {}
            paraphrase['speaker'] = item['message']['speaker']
            paraphrase['text'] = item['message']['text']
            paraphrase['critical'] = item['message'].get('paraphrase_critical', False)
            paraphrase['polite'] = item['message'].get('paraphrase_polite', False)
            turn['paraphrase'] = paraphrase
        # norm occurence, can be multiple ones
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'norm_occurrence':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            if turn.get('norms', None) is None:
                turn['norms'] = []
            turn['norms'].append({
                'norm': item['message']['norm'],
                'status': item['message']['status'],
            })
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'valence':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['valence'] = item['message']['level']
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'arousal':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            turn['arousal'] = item['message']['level']
        if item.get('queue', False) == 'ACTION' and item.get('message', {}).get('type', False) == 'hololens' and (item.get('message', {}).get('prefix', False) == 'alert' or item.get('message', {}).get('prefix', False) == 'late') :
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            if turn.get('actions', None) is None:
                turn['actions'] = []
            message = item['message']['display'].replace('<i>', '').replace('</i>', '')
            if not any(d.get('display', False) == message for d in turn['actions']):
                turn['actions'].append({
                    'display': message,
                    'delayed': item.get('message', {}).get('prefix', False) == 'late'
                })
        if item.get('queue', False) == 'ACTION' and item.get('message', {}).get('type', False) == 'hololens' and (item.get('message', {}).get('remediation', False) == 'Auto' or 'Added:' in item.get('message', {}).get('display', '')):
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'], item['time_seconds'])
            if turn.get('rephrase', None) is None:
                turn['rephrase'] = []
            if not any(d.get('display', False) == item['message']['display'] for d in turn['rephrase']):
                turn['rephrase'].append({
                    'display': item['message']['display'],
                })

    output = []
    for item in turns:
        if item.get('ASRText', None) is not None:
            output.append(item)
    # with open('ptt-status.json', 'w') as outfile:
    #     json.dump(ptt_turns, outfile, ensure_ascii=False, indent=True)
    #     outfile.write('\n')

    return output

def convert_output_to_tracks(output, width=1920, height=1080, framerate=30, offset=5):
    tracks = {}
    count = 0
    offset_frames = framerate * offset
    beginning_offset = 0
    for index, item in enumerate(output):
        start_frame = offset_frames + (framerate * item['startTime']) - beginning_offset
        if index == 0:
            beginning_offset = offset_frames
        if (index + 1) < len(output):

            current_endtime = offset_frames + (framerate * item['endTime'])
            next_start_time = offset_frames + (framerate * output[index + 1]['startTime']) + beginning_offset
            current_start_global = item['startglobal']
            next_end_global = output[index + 1]['endglobal']
            time_length = next_end_global - current_start_global
            # split the difference
            end_frame = start_frame + (framerate * time_length)
        else:
            end_frame = offset_frames + (framerate * item['endTime'])
        track = {
            "begin": int(start_frame),
            "end": int(end_frame),
            "id": count,
            "confidencePairs": [
                [
                    "turn",
                    1.0
                ]
            ],
            "attributes": {
                "ASRText": item["ASRText"],
                "speaker": item["speaker"],

            },
            "features": [
                {
                    "frame": int(start_frame),
                    "bounds": [
                        0,
                        0,
                        1920,
                        1080
                    ],
                    "interpolate": True,
                    "keyframe": True,
                    "attributes": {}
                },
                                {
                    "frame": int(end_frame),
                    "bounds": [
                        0,
                        0,
                        1920,
                        1080
                    ],
                    "interpolate": True,
                    "keyframe": True,
                    "attributes": {}
                }
            ]

        }
        translation = None
        sourceLanguage = None
        targetLanguage = None

        if item.get('translation', False):
            translation = item['translation']['text']
            sourceLanguage = item['translation']['source_language']
            targetLanguage = item['translation']['target_language']
            track['attributes']['translation'] = translation
            track['attributes']['sourceLanguage'] = sourceLanguage
            track['attributes']['targetLanguage'] = targetLanguage
        if item.get('rephrase_translation', False):
            track['attributes']['rephrase_translation'] = []
            for rehprase_translation in item['rephrase_translation']:
                translation = rehprase_translation['text']
                sourceText = rehprase_translation['sourceText']
                if not any(d.get('translation') == translation for d in track['attributes']['rephrase_translation']):
                    track['attributes']['rephrase_translation'].append({
                        "translation": translation,
                        "sourceText": sourceText,
                    })

        emotions = None
        if item.get('emotions', False):
            emotions = item['emotions']
            track['attributes']['emotions'] = emotions
        if item.get('valence', False):
            track['attributes']['valence'] = item['valence']
        if item.get('arousal', False):
            track['attributes']['arousal'] = item['arousal']
        if item.get('norms', False):
            track['attributes']['norms'] = item['norms']
        if item.get('actions', False):
            track['attributes']['alerts'] = item['actions']
        if item.get('rephrase', False):
            track['attributes']['rephrase'] = item['rephrase']
        tracks[count] = track
        count += 1

    trackJSON = {"tracks": tracks, "groups": {}, "version": 2}

    return trackJSON

if __name__ == '__main__':
    run_script()


