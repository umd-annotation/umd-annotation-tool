import os
import click
import json
import math
import girder_client
apiURL = "annotation.umd.edu" # localhost
apiPort = 443 # 8000


baseNormMap = {
    "Apology": 101,
    "Criticism": 102,
    "Greeting": 103,
    "Request": 104,
    "Persuasion": 105,
    "Thanks": 106,
    "Taking Leave": 107,
    "Admiration": 108,
    "Finalizing Negotiation/Deal": 109,
    "Refusing a Request": 110,
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
        normMap[str(item['named'])] = int(item['id'])


def bin_value(value):
    return math.floor(value / 200) + 1


def export_changepoints(tracks):
    rows = []
    fps = 30
    for t in tracks:
            if 'features' in t.keys():
                features = t['features']
                userDataFound = {}
                for feature in features:
                    if 'attributes' in feature.keys():
                        attributes = feature['attributes']
                        for key in attributes.keys():
                            if '_Impact' in key:
                                login = key.replace('_Impact', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Impact'] = attributes[key]
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * feature['frame']
                            if '_Comment' in key:
                                login = key.replace('_Comment', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Comment'] = attributes[key]
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * feature['frame']

                for key in userDataFound.keys():
                    columns = [
                        key,
                        'name',
                        userDataFound[key]['Timestamp'],
                        userDataFound[key]['Impact'],
                        userDataFound[key]['Comment'],
                    ]
                    rows.append(columns)
    return rows

def export_remediation(tracks):
    row = []
    for t in tracks:
            if 'features' in t.keys():
                features = t['features']
                userDataFound = {}
                for feature in features:
                    if 'attributes' in feature.keys():
                        attributes = feature['attributes']
                        for key in attributes.keys():
                            if '_RemediationComment' in key:
                                login = key.replace('_RemediationComment', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Comment'] = attributes[key]
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * feature['frame']

                for key in userDataFound.keys():
                    columns = [
                        key,
                        'name',
                        userDataFound[key]['Timestamp'],
                        userDataFound[key]['Comment'],
                    ]
                    row.append(columns)
    return row

def export_norms(tracks):
    rows = []
    videoname = 'name'
    for t in tracks:
            if 'attributes' in t.keys():
                attributes = t['attributes']
                userDataFound = {}
                for key in attributes.keys():
                    if '_Norms' in key:
                        login = key.replace('_Norms', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        norms = attributes[key]
                        for normKey in norms.keys():
                            if normKey in normMap.keys():
                                # record the norm
                                userDataFound[mapped][normMap[normKey]] = norms[normKey]
                for key in userDataFound.keys():
                    for normKey in userDataFound[key].keys():
                        columns = [
                            key,
                            videoname,
                            f'{videoname}_{t["id"]:04}',
                            normKey,
                            userDataFound[key][normKey],
                        ]
                        rows.append(columns)
    return rows

def export_valence(tracks):
    videoname = 'name'
    rows = []
    for t in tracks:
            if 'attributes' in t.keys():
                attributes = t['attributes']
                userDataFound = {}
                for key in attributes.keys():
                    if '_Valence' in key:
                        login = key.replace('_Valence', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        userDataFound[mapped]['valence_continuous'] = attributes[key]
                        userDataFound[mapped]['valence_binned'] = bin_value(attributes[key])
                    if '_Arousal' in key:
                        login = key.replace('_Arousal', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        userDataFound[mapped]['arousal_continuous'] = attributes[key]
                        userDataFound[mapped]['arousal_binned'] = bin_value(attributes[key])
                for key in userDataFound.keys():
                    columns = [
                        key,
                        videoname,
                        f'{videoname}_{t["id"]:04}',
                        userDataFound[key]['valence_continuous'],
                        userDataFound[key]['valence_binned'],
                        userDataFound[key]['arousal_continuous'],
                        userDataFound[key]['arousal_binned'],
                    ]
                    rows.append(columns)
    return rows

def export_emotions(tracks):
    videoname = ''
    rows = []
    for t in tracks:
            if 'attributes' in t.keys():
                attributes = t['attributes']
                userDataFound = {}
                for key in attributes.keys():
                    if '_Emotions' in key:
                        login = key.replace('_Emotions', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        base = ','.join(attributes[key].split('_'))
                        userDataFound[mapped]['Emotions'] = base
                    if '_MultiSpeaker' in key:
                        login = key.replace('_MultiSpeaker', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        userDataFound[mapped]['MultiSpeaker'] = attributes[key]
                for key in userDataFound.keys():
                    columns = [
                        key,
                        videoname,
                        f'{videoname}_{t["id"]:04}',
                        f'"{userDataFound[key]["Emotions"]}"',
                        userDataFound[key]['MultiSpeaker'],
                    ]
                    rows.append(columns)
    return rows

def export_versions_per_file(tracks):
    fps = 30
    emotions_count = 0
    norms_count = 0
    valence_arousal_count = 0
    change_point_count = 0
    name = 'name'
    for t in tracks:
            if 'features' in t.keys():
                features = t['features']
                userDataFound = {}
                if 'attributes' in t.keys():
                    track_attributes = t['attributes']

                    for key in track_attributes.keys():
                        if '_Emotions' in key:
                            emotions_count += 1
                        if '_Valence' in key:
                            valence_arousal_count += 1
                        if '_Norms' in key:
                            norms_count += 1
                for feature in features:
                    if 'attributes' in feature.keys():
                        attributes = feature['attributes']
                        for key in attributes.keys():
                            if '_Impact' in key:
                                change_point_count += 1
                            if '_Comment' in key:
                                login = key.replace('_Comment', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Comment'] = attributes[key]
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * feature['frame']
    columns = [name, emotions_count, valence_arousal_count, norms_count, change_point_count ]
    return columns

@click.command(
    name="Generate Tracks",
    help="Takes a video and meta config and generates a track file",
)
@click.argument("jsonfile")
def load_data(jsonfile):
    gc = login()
    get_server_normMap(gc)
    with open(jsonfile, 'r') as myfile:
        file_data = myfile.read()
        data = json.loads(file_data)
        changepoints = export_changepoints(list(data['tracks'].values()))
        emotions = export_emotions(list(data['tracks'].values()))
        remediations = export_remediation(list(data['tracks'].values()))
        valence = export_valence(list(data['tracks'].values()))
        norms = export_norms(list(data['tracks'].values()))
        versions_per_file = export_versions_per_file(list(data['tracks'].values()))
        print(versions_per_file)


if __name__ == "__main__":
    load_data()