import argparse
import json
import os
import girder_client
apiURL = "localhost" # "annotation.umd.edu" # localhost
apiPort = 8010

baseNormMap = {
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
    '117': 'Complaining',
    '118': 'Topic Closing',
    '119': 'Giving Advice',
    "none": "None",
}
normMap = {}

def login():
    gc = girder_client.GirderClient(apiURL, port=apiPort, apiRoot='girder/api/v1' )
    gc.authenticate(interactive=True)
    return gc


def get_server_normMap(gc: girder_client.GirderClient):
    global normMap
    data = gc.get('/UMD_configuration/TA2_config')
    norms = data['normMap']
    normMap = baseNormMap
    for item in norms:
        print(item)
        normMap[str(item['id'])] = item['named']


def try_open_file(input_file):
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as infile:
                data = infile.read()  # Test read to check if encoding works
            print(f"Successfully read {input_file} with encoding: {encoding}")
            return encoding  # Return the encoding that works
        except UnicodeDecodeError:
            print(f"Encoding {encoding} failed for file: {input_file}")
    raise UnicodeDecodeError(f"None of the tested encodings worked for file: {input_file}")


def remove_base64_from_jsonl(input_file, output_file):
    output = []
    raw = []
    encoding = try_open_file(input_file)  # Find a working encoding

    with open(input_file, 'r', encoding=encoding) as infile:
        for line in infile:
            if not line.strip().startswith('#'):  # Skip lines starting with #
                data = json.loads(line)
                if 'queue' in data.keys():
                    if 'VIDEO_MAIN' == data['queue']:
                        if data.get('message', {}).get('image', False):
                            del data['message']['image']
                        raw.append(data)
                        continue
                    if 'CONTROL' == data['queue']:
                        raw.append(data)                    
                        continue
                    if 'AUDIO_SELF' == data['queue'] and  (data['message']['type'] == 'audio_status' and data['message']['status'] in ['ptt-pressed', 'ptt-released']):
                        output.append(data)

                if 'message' in data and isinstance(data['message'], dict):
                    if 'original_text' in data['message']:
                        original_text = data['message']['original_text']
                        # Convert unicode to UTF-8 encoding
                        data['message']['original_text'] = original_text.encode('utf-8').decode('utf-8')
                    if 'image' in data['message']:
                        print('Deleting Image')
                        del data['message']['image']
                    if 'audio' in data['message']:
                        del data['message']['audio']
                    if 'type' in data['message']:
                        if data['message']['type'] in  ['webcam', 'image_ready', 'check-status', 'image_start', 'pipeline_response', 'pipeline_request', 'control', 'audio_status']:                            
                            raw.append(data)
                            continue
                        if data['message']['type'] == 'norm_occurrence' and data['message']['name']:
                            if normMap.get(str(data['message']['name'])):
                                data['message']['norm'] = normMap[str(data['message']['name'])]
                raw.append(data)                    
                output.append(data)
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump(raw, outfile, ensure_ascii=False, indent=True)  # ensure_ascii=False to output UTF-8 properly
        return output

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.jsonl'):
                input_file = os.path.join(root, file)
                file_name, _ = os.path.splitext(file)
                output_file = os.path.join(root, file_name + '_converted.json')
                print("Processing:", input_file)
                remove_base64_from_jsonl(input_file, output_file)
                print("Base64 data removed and saved to:", output_file)

def main():
    gc = login()
    get_server_normMap(gc)
    parser = argparse.ArgumentParser(description='Process JSONL files in a folder and remove base64 data from them.')
    parser.add_argument('folder_path', help='Folder path containing JSONL files')
    args = parser.parse_args()

    process_folder(args.folder_path)

if __name__ == "__main__":
    main()
