import json
import base64
import click

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


def remove_base64_from_jsonl(input_file, output_file):
    output = []
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if not line.strip().startswith('#'):  # Skip lines starting with #
                data = json.loads(line)
                if 'queue' in data.keys():
                    if 'VIDEO_MAIN' == data['queue']:
                        continue
                    if 'CONTROL' == data['queue']:
                        continue
                if 'message' in data and isinstance(data['message'], dict):
                    if 'original_text' in data['message']:
                        original_text = data['message']['original_text']
                        # Convert unicode to UTF-8 encoding
                        data['message']['original_text'] = original_text.encode('utf-8').decode('utf-8')
                    if 'image' in data['message']:
                        print('Deleting Image')
                        del data['message']['image']
                    if 'audio' in data['message']:
                        print('Deleting Audio')
                        del data['message']['audio']
                    if 'type' in data['message']:
                        if data['message']['type'] in  ['webcam', 'image_ready', 'check-status' , 'image_start', 'pipeline_response', 'pipeline_request', 'control', 'audio_status']:
                            continue
                        if data['message']['type'] == 'norm_occurrence' and data['message']['name']:
                            if normMap[str(data['message']['name'])]:
                                data['message']['norm'] = normMap[str(data['message']['name'])]
                output.append(data)
        json.dump(output, outfile, ensure_ascii=False, indent=True)  # ensure_ascii=False to output UTF-8 properly
        outfile.write('\n')
        return output


def create_or_get_turn(turns, start_time, end_time):
    
    for item in turns:
        if item['startTime'] == start_time and item['endTime'] == end_time:
            return item
    turn = {
        'startTime': start_time,
        'endTime': end_time,
    }
    turns.append(turn)
    return turn


def process_outputjson(output):
    turns = []
    print('processing output file')
    for item in output:
        # we have a turn with ASR information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'asr_result':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            turn['ASRText'] = item['message']['asr_text']
            turn['speaker'] = item['message']['speaker']
        # translation information
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'translation':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            turn['translation'] = {
                'source_language': item['message']['source_language'],
                'target_language': item['message']['target_language'],
                'speaker': item['message']['speaker'],
                'text': item['message']['translation'],
            }
        # storing emotions for future use
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('asr_type', False) == 'TURN' and item.get('message', {}).get('type', False) == 'sri_emotions':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            turn['emotions'] = item['message']['emotions']
        # intent and rudeness
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'intent_and_rudeness':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
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
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            paraphrase = {}
            paraphrase['speaker'] = item['message']['speaker']
            paraphrase['text'] = item['message']['text']
            paraphrase['critical'] = item['message'].get('paraphrase_critical', False)
            paraphrase['polite'] = item['message'].get('paraphrase_polite', False)
            turn['paraphrase'] = paraphrase
        # norm occurence, can be multiple ones
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'norm_occurrence':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            print(f"NORMS EXISTENCE: {turn.get('norms', None)}")
            if turn.get('norms', None) is None:
                turn['norms'] = []
            turn['norms'].append({
                'norm': item['message']['norm'],
                'status': item['message']['status'],
            })
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'valence':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            turn['valence'] = item['message']['level']
        if item.get('queue', False) == 'RESULT' and item.get('message', {}).get('type', False) == 'arousal':
            turn = create_or_get_turn(turns, item['message']['start_seconds'], item['message']['end_seconds'])
            turn['arousal'] = item['message']['level']

    output = []
    for item in turns:
        if item.get('ASRText', None) is not None:
            output.append(item)

    return output

def convert_output_to_tracks(output, width=1920, height=1080, framerate=30, offset=5):
    tracks = {}
    count = 0
    offset_frames = framerate * offset
    for item in output:
        start_frame = offset_frames + (framerate * item['startTime'])
        end_frame = offset_frames + (framerate * item['endTime'])
        track = {
            "begin": start_frame,
            "end":end_frame,
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
                    "frame": start_frame,
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
                    "frame": end_frame,
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
            track['translation'] = translation
            track['sourceLanguage'] = sourceLanguage
            track['targetLanguage'] = targetLanguage
        emotions = None
        if item.get('emotions', False):
            emotions = item['emotions']
            track['emotions'] = emotions
        if item.get('valence', False):
            track['valence'] = item['valence']
            track['arousal'] = item['arousal']
        if item.get('norms', False):
            track['norms'] = item['norms']
        tracks[count] = track
        count += 1

    trackJSON = {"tracks": tracks, "groups": {}, "version": 2}

    return trackJSON

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def main_script(input_file, output_file):
    output = remove_base64_from_jsonl(input_file, output_file)
    turns = process_outputjson(output)
    print(turns)
    with open('turns.json', 'w') as outfile:
        json.dump(turns, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')
    trackJSON = convert_output_to_tracks(turns)
    with open('tracks.json', 'w') as outfile:
        json.dump(trackJSON, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')


if __name__ == '__main__':
    main_script()
