import girder_client
import json
import click
import requests
import csv
import os
from fuzzywuzzy import process
from bs4 import BeautifulSoup


UPDATE_EXISTING_MESSAGES = True  # Updates existing messages with any new data while preserving older annotations
NEW_DISPLAY_DATA = True  # Adds the new Final, Buttons, Remediation Decision ('Auto', 'Interactive', 'Passivie')
ADD_CLNG_VIDEOS = True  # will add the CLNG labelled videos with TURN creation links
JSONLSourceFolderId = "6627ef547193244a6e33353d"  # the GirderId of the folder that contains the source JSONL files
VideoSourceFolderIds = ["667c58b582915211ce417b78"]  # folders to search for matching Video files
CloneDestinationFolderId = "661e8fceaee0d357e2455d47"  # destination girder folder ID for the cloned videos

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



def extract_CLNG_videos(video_dict):
    unAnnotatedVideos = {}
    for key in video_dict.keys():
        if 'CLNG' in key:
            unAnnotatedVideos[key] = video_dict[key]
    return unAnnotatedVideos


# Function to generate row for each object
def generate_row(obj, base_url):
    row = [obj["name"]]
    row.append(f"{base_url}/#/viewer/{obj['id']}?mode=TA2Annotation_ASRMTQuality")
    row.append(f"{base_url}/#/viewer/{obj['id']}?mode=TA2Annotation_Norms")
    row.append(f"{base_url}/#/viewer/{obj['id']}?mode=TA2Annotation_Remediation")
    if obj.get("CLNG", False):
        row.append(f"{base_url}/#/viewer/{obj['id']}?mode=TA2Annotation_Creation")
    return row

def generate_CSV(objects, base_url):
    # Writing to CSV
    with open('TA2Annotations.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Writing header
        csvwriter.writerow(['NAME', 'TA2 Annotation Quality', 'TA2 Norms', 'TA2 Remediation', 'TA2 Turn Creation'])
        # Writing data rows
        for obj in objects:
            csvwriter.writerow(generate_row(obj, base_url))

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
    translations = []
    ptt_turns = []
    for item in output:
        start_seconds = item['message'].get('start_seconds', False)
        if not start_seconds:
            start_seconds = item['message'].get('start_time')
        end_seconds = item['message'].get('end_seconds', False)
        if not end_seconds:
            end_seconds = item['message'].get('end_time')
        if item.get('queue', False) == 'AUDIO_SELF' and item.get('message', {}).get('status', False) in ['ptt-pressed', 'ptt-released']:
            ptt_turns.append({
                "status": item.get('message', {}).get('status', False),
                "seconds": item.get('time_seconds')
            })
        # we have a turn with ASR information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'asr_result':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            turn['ASRText'] = item['message']['asr_text']
            turn['speaker'] = item['message']['speaker']
        # translation information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'translation':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            turn['translation'] = {
                'source_language': item['message']['source_language'],
                'target_language': item['message']['target_language'],
                'speaker': item['message']['speaker'],
                'text': item['message']['translation'],
            }
        # translation of possible Rephrasing
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TEXT' and item.get('message', {}).get('type', False) == 'translation':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
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
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            turn['emotions'] = item['message']['emotions']
        # intent and rudeness
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'intent_and_rudeness':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
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
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            paraphrase = {}
            paraphrase['speaker'] = item['message']['speaker']
            paraphrase['text'] = item['message']['text']
            paraphrase['critical'] = item['message'].get('paraphrase_critical', False)
            paraphrase['polite'] = item['message'].get('paraphrase_polite', False)
            turn['paraphrase'] = paraphrase
        # norm occurence, can be multiple ones
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'norm_occurrence':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            if turn.get('norms', None) is None:
                turn['norms'] = []
            norm = item['message'].get('norm', False);
            if not norm:
                normId = item['message'].get('name', False)
                if normId:
                    norm = normMap.get(normId)
            if norm:
                turn['norms'].append({
                    'norm': norm,
                    'status': item['message']['status'],
                })
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'valence':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            turn['valence'] = item['message']['level']
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'arousal':
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            turn['arousal'] = item['message']['level']
        if item.get('queue', False) == 'ACTION' and item.get('message', {}).get('type', False) == 'hololens' and (item.get('message', {}).get('prefix', False) == 'alert' or item.get('message', {}).get('prefix', False) == 'late') :
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            message = item['message']['display'].replace('<i>', '').replace('</i>', '')
            if not any(d.get('display', False) == message for d in turn['actions']):
                if turn.get('actions', None) is None:
                    turn['actions'] = []
                turn['actions'].append({
                    'display': message,
                    'delayed': item.get('message', {}).get('prefix', False) == 'late'
                })
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'ccu_to_v2v' and item.get('message', {}).get('alert', False):
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            message = item['message']['alert']['text']
            soup = BeautifulSoup(message, "html.parser")
            if turn.get('actions', None) is None:
                turn['actions'] = []
            turn['actions'].append({
                'display': soup.get_text(),
            })
        if NEW_DISPLAY_DATA and item.get('message', {}).get('is_final', False) and item.get('message', {}).get('text', False):
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            text = item.get('message', {}).get('text', False)
            if turn.get('actions', None) is None:
                turn['actions'] = []
            turn['actions'].append({
                'display': f'Final user Utterance: {text}',
            })


            



        if item.get('queue', False) == 'ACTION' and item.get('message', {}).get('type', False) == 'hololens' and (item.get('message', {}).get('remediation', False) == 'Auto' or 'Added:' in item.get('message', {}).get('display', '')):
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            if not any(d.get('display', False) == item['message']['display'] for d in turn['rephrase']):
                if turn.get('rephrase', None) is None:
                    turn['rephrase'] = []
                turn['rephrase'].append({
                    'display': item['message']['display'],
                })

        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('remediation_text', {}).get('displayTokens', False):
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            display_list = item.get('message', {}).get('remediation_text', {}).get('displayTokens', [])
            for text_item in display_list:
                if text_item.get('text', False):
                    message = text_item.get('text', '')
                    soup = BeautifulSoup(message, "html.parser")
                    stripped_text = soup.get_text().strip()
                    if len(stripped_text) > 0:
                        if "Rephrased:" in stripped_text:
                            already_in_list = False
                            for rephrase in turn.get('rephrase', {}):
                                if stripped_text in rephrase['display']:
                                    already_in_list = True
                                    break
                            if not already_in_list:
                                if turn.get('rephrase', None) is None:
                                    turn['rephrase'] = []
                                turn['rephrase'].append({
                                    "display": stripped_text
                                })
                        else:
                            already_in_list = False
                            for actions in turn.get('actions', []):
                                if stripped_text in actions['display']:
                                    already_in_list = True
                                    break
                            if not already_in_list and stripped_text != 'Taboo violation':
                                if turn.get('actions', None) is None:
                                    turn['actions'] = []
                                turn['actions'].append({
                                    'display': stripped_text,
                                })
            if NEW_DISPLAY_DATA:
                button_list = item.get('message', {}).get('remediation_text', {}).get('buttons', [])
                for item in button_list:
                    text = item.get('text', False)
                    soup = BeautifulSoup(text, "html.parser")
                    if text:
                        if turn.get('actions', None) is None:
                            turn['actions'] = []
                        turn['actions'].append({
                            'display': f'Button: {soup.get_text()}',
                        })
                remediation_decision = item.get('message', {}).get('remediation', False)
                if remediation_decision:
                    if turn.get('actions', None) is None:
                        turn['actions'] = []
                    turn['actions'].append({
                        'display': f'Remediation Decision: {remediation_decision}',
                    })



        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'taboo_result' and len(item.get('message', {}).get('taboo_reason', "")) > 0:
            turn = create_or_get_turn(turns, start_seconds, end_seconds, item['time_seconds'])
            message = item['message']['taboo_reason']
            if turn.get('actions', None) is None:
                turn['actions'] = []
            turn['actions'].append({
                'display': f"Taboo Violated Reason: {message}",
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

def replace_exising_alerts(gc: girder_client.GirderClient, existing_id, newTrackFilePath):
    downloaded_tracks = gc.get(f'dive_annotation/track?sort=id&sortdir=1&folderId={existing_id}')
    # convert into trackJson file
    temp_track_map = {}
    for item in downloaded_tracks:
        temp_track_map[item['id']] = item
    existing_track_data = {
        'tracks':  temp_track_map,
        'groups': {},
        'version': 2,
    }
    # now we want to load up the newTrack data
    with open(newTrackFilePath, 'r', encoding='utf8') as f:
        new_track_file = json.load(f)
    existing_tracks = existing_track_data['tracks']
    new_tracks = new_track_file['tracks']
    if len(new_tracks.keys()) != len(existing_tracks.keys()):
        print('ERROR: Existing tracks and New Track Turns are different')
        return
    keys = existing_tracks.keys()
    # now a trackId basis we update the track['attributes']['alerts'] to the new data
    for key in new_tracks:
        track = new_tracks[key]
        if track.get('attributes', {}).get('alerts'):
            existing_tracks[track['id']]['attributes']['alerts'] = track['attributes']['alerts']
    # now we can place the updated file in a location
    if not os.path.exists('./updated_tracks'):
        os.mkdir('./updated_tracks')
    updatedTrackPath = f'{os.path.basename(newTrackFilePath).replace(".json","_updatedAlerts.json")}'
    existing_track_data['tracks'] = existing_tracks
    with open(f'./updated_tracks/{updatedTrackPath}', 'w', encoding='utf8') as outfile:
        json.dump(existing_track_data, outfile, ensure_ascii=False, indent=True)
    upload_track_json(gc, existing_id, f'./updated_tracks/{updatedTrackPath}')


@click.command(name="cloneAndConvert", help="Load in ")
def run_script():
    gc = login()
    video_map = get_processVideos(gc)
    clng_videos = extract_CLNG_videos(video_map)
    existing_videos = get_existingVideos(gc, CloneDestinationFolderId)
    processed_map = get_processJSONItems(gc, JSONLSourceFolderId)
    matching, unmatching = get_matching_items(video_map, processed_map)
    # write the unmatched items to unmatching.json
    with open('unmatching.json', 'w', encoding='utf8') as outfile:
        json.dump(unmatching, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')

    count = 0
    limit = 9999
    completed_videos = []
    for key in matching.keys():
        if key in existing_videos.keys():
            completed_videos.append({'name': key, 'id': existing_videos[key]})
            if UPDATE_EXISTING_MESSAGES:
                item = matching[key]
                trackJSONFilePath = download_and_process_json(gc, item["jsonId"], f"{key}.json")
                item["trackJSON"] = trackJSONFilePath
                print(f'Updating Messages for video: {key}')
                replace_exising_alerts(gc, existing_videos[key], trackJSONFilePath)
                continue
            else:
                print(f'Skipping video: {key} it already exists')
            continue
        item = matching[key]
        trackJSONFilePath = download_and_process_json(gc, item["jsonId"], f"{key}.json")
        item["trackJSON"] = trackJSONFilePath
        cloneId = clone_video_folder(gc, item["videoId"], key, CloneDestinationFolderId)
        item["cloneId"] = cloneId
        upload_track_json(gc, cloneId, trackJSONFilePath)
        completed_videos.append({'name': key, 'id': cloneId})
        print(f"Completed: {key}")
        count += 1
        if count > limit:
            break
    if ADD_CLNG_VIDEOS:
        for key in clng_videos.keys():
            if key in existing_videos.keys():
                completed_videos.append({'name': key, 'id': existing_videos[key], 'CLNG': True})
                print(f'Skipping video: {key} it already exists')
                continue
            item = clng_videos[key]
            cloneId = clone_video_folder(gc, item, key, CloneDestinationFolderId)
            gc.addMetadataToFolder(cloneId, {"UMDAnnotation": "TA2"})
            trackJSON = {"tracks": {}, "groups": {}, "version": 2}
            with open('emptyTracks.json', 'w', encoding='utf8') as outfile:
                json.dump(trackJSON, outfile, ensure_ascii=False, indent=True)
            gc.uploadFileToFolder(cloneId, 'emptyTracks.json')
            gc.sendRestRequest('POST', f'dive_rpc/postprocess/{cloneId}', data={'skipTranscoding': True, 'skipJobs': True})
            completed_videos.append({'name': key, 'id': cloneId, 'CLNG': True})

    generate_CSV(completed_videos, f'https://{apiURL}')

if __name__ == '__main__':
    run_script()


