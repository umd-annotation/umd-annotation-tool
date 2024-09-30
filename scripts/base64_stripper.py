import json
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




def remove_base64_from_jsonl(input_file, output_file):
    output = []
    raw = []
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
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
                        print('Deleting Audio')
                        del data['message']['audio']
                    if 'type' in data['message']:
                        if data['message']['type'] in  ['webcam', 'image_ready', 'check-status', 'image_start', 'pipeline_response', 'pipeline_request', 'control', 'audio_status']:                            
                            raw.append(data)
                            continue
                        if data['message']['type'] == 'norm_occurrence' and data['message']['name']:
                            if normMap[str(data['message']['name'])]:
                                data['message']['norm'] = normMap[str(data['message']['name'])]
                raw.append(data)                    
                output.append(data)
        with open('raw.json', 'w') as rawout:
            json.dump(raw, rawout, ensure_ascii=False, indent=True)  # ensure_ascii=False to output UTF-8 properly
        json.dump(output, outfile, ensure_ascii=False, indent=True)  # ensure_ascii=False to output UTF-8 properly
        outfile.write('\n')
        return output

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def main_script(input_file, output_file):
    output = remove_base64_from_jsonl(input_file, output_file)
    with open('output.json', 'w') as outfile:
        json.dump(output, outfile, ensure_ascii=False, indent=True)
        outfile.write('\n')


if __name__ == '__main__':
    main_script()
