import csv
import io
import json
import math
from pathlib import Path

from dive_server import crud_annotation
from girder.constants import AccessType
from girder.models.folder import Folder
from girder.models.user import User
from girder.utility import ziputil

normMap = {
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


def bin_value(value):
    return math.floor(value / 200) + 1


def export_changepoint_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "timestamp", "impact_scalar", "comment"])
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
                    videoname,
                    userDataFound[key]['Timestamp'],
                    userDataFound[key]['Impact'],
                    userDataFound[key]['Comment'],
                ]
                writer.writerow(columns)
                yield csvFile.getvalue()
                csvFile.seek(0)
                csvFile.truncate(0)
    yield csvFile.getvalue()


def export_remediation_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "timestamp", "comment"])
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
                    videoname,
                    userDataFound[key]['Timestamp'],
                    userDataFound[key]['Comment'],
                ]
                writer.writerow(columns)
                yield csvFile.getvalue()
                csvFile.seek(0)
                csvFile.truncate(0)
    yield csvFile.getvalue()


def export_norms_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerow(
        [
            "user_id",
            "file_id",
            "segment_id",
            "norm",
            "status",
        ]
    )
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
                    writer.writerow(columns)
                    yield csvFile.getvalue()
                    csvFile.seek(0)
                    csvFile.truncate(0)
    yield csvFile.getvalue()


def export_valence_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerow(
        [
            "user_id",
            "file_id",
            "segment_id",
            "valence_continuous",
            "valence_binned",
            "arousal_continuous",
            "arousal_binned",
        ]
    )
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
                writer.writerow(columns)
                yield csvFile.getvalue()
                csvFile.seek(0)
                csvFile.truncate(0)
    yield csvFile.getvalue()


def export_segment_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerow(
        [
            "file_id",
            "segment_id",
            "start",
            "end",
        ]
    )
    for t in tracks:
        start = t['begin'] * (1 / fps)
        end = t['end'] * (1 / fps)
        columns = [videoname, f'{videoname}_{t["id"]:04}', start, end]
        writer.writerow(columns)
        yield csvFile.getvalue()
        csvFile.seek(0)
        csvFile.truncate(0)
    yield csvFile.getvalue()


def export_emotions_tab(tracks, videoname, fps, userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "segment_id", "emotion", "multi_speaker"])
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
                writer.writerow(columns)
                yield csvFile.getvalue()
                csvFile.seek(0)
                csvFile.truncate(0)
    yield csvFile.getvalue()


def generate_tab(tracks, videoname, fps, userMap, type):
    def downloadGenerator():
        if type == 'segment':
            for data in export_segment_tab(tracks, videoname, fps, userMap):
                yield data
        if type == 'valence':
            for data in export_valence_tab(tracks, videoname, fps, userMap):
                yield data
        if type == 'emotions':
            for data in export_emotions_tab(tracks, videoname, fps, userMap):
                yield data
        if type == 'norms':
            for data in export_norms_tab(tracks, videoname, fps, userMap):
                yield data
        if type == 'changepoint':
            for data in export_changepoint_tab(tracks, videoname, fps, userMap):
                yield data
        if type == 'remediation':
            for data in export_remediation_tab(tracks, videoname, fps, userMap):
                yield data

    return downloadGenerator


def convert_to_zips(folders, userMap, user):
    def stream():
        z = ziputil.ZipGenerator()
        for folderId in folders:
            folder = Folder().load(folderId, level=AccessType.READ, user=user)
            videoname = folder['name']
            fps = folder['meta']['fps']
            tracks = crud_annotation.TrackItem().list(folder)
            if len(folders) == 1:
                zip_path = './'
            else:
                zip_path = f'./{folder["name"].replace(".mp4","")}/'

            def makeDiveJson():
                """Include DIVE JSON output annotation file"""
                annotations = crud_annotation.get_annotations(folder)
                print(annotations)
                yield json.dumps(annotations)

            for data in z.addFile(makeDiveJson, Path(f'{zip_path}annotations.json')):
                yield data
            seg_gen = generate_tab(tracks, videoname, fps, userMap, 'segment')
            for data in z.addFile(seg_gen, Path(f'{zip_path}segment_tab.tab')):
                yield data
            tracks.rewind()
            valence_gen = generate_tab(tracks, videoname, fps, userMap, 'valence')
            for data in z.addFile(valence_gen, Path(f'{zip_path}valence_tab.tab')):
                yield data
            tracks.rewind()
            emotion_gen = generate_tab(tracks, videoname, fps, userMap, 'emotions')
            for data in z.addFile(emotion_gen, Path(f'{zip_path}emotions_tab.tab')):
                yield data
            tracks.rewind()
            norm_gen = generate_tab(tracks, videoname, fps, userMap, 'norms')
            for data in z.addFile(norm_gen, Path(f'{zip_path}norms_tab.tab')):
                yield data
            tracks.rewind()
            norm_gen = generate_tab(tracks, videoname, fps, userMap, 'changepoint')
            for data in z.addFile(norm_gen, Path(f'{zip_path}changepoint_tab.tab')):
                yield data
            tracks.rewind()
            norm_gen = generate_tab(tracks, videoname, fps, userMap, 'remediation')
            for data in z.addFile(norm_gen, Path(f'{zip_path}remediation_tab.tab')):
                yield data
        yield z.footer()

    return stream

def generate_links_tab(url, folders):
    def downloadGenerator():
        for data in export_links_tab(url, folders):
            yield data

    return downloadGenerator

def export_links_tab(url, folders):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerow(
        [
            "Name",
            "LC",
            "CONDITION",
            "SCENARIO"
            "FLE",
            "SME",
            "DATE",
            "PERSON",
            "PERSPECTIVE",
            "V/A/E",
            "Norms",
            "Changepoint",
            "Remediation",
        ]
    )
    for folder in folders:
        name = folder['name'].replace('.mp4', '').replace('Video', '')
        LC = ''
        CONDITION = ''
        SCENARIO = ''
        FLE = ''
        SME = ''
        DATE = ''
        PERSON = ''
        PERSPECTIVE = ''
        splits = name.split('_')
        if len(splits) >= 6:
            LC = splits[0]
            CONDITION = splits[1]
            SCENARIO = splits[2]
            FLE = splits[3]
            SME = splits[4]
            DATE = splits[5]
            PERSON = splits[6]
            if len(splits) and '-' in PERSON:
                person_split = PERSON.split('-')
                PERSON = person_split[0]
                PERSPECTIVE = person_split[1]

        root = f'{url}/viewer/{folder["_id"]}?mode='
        vae = f'{root}VAE'
        norms = f'{root}norms'
        changepoint = f'{root}changepoint'
        remediation = f'{root}remediation'
        columns = [ 
            name,
            LC,
            CONDITION,
            SCENARIO,
            FLE,
            SME,
            DATE,
            PERSON,
            PERSPECTIVE,
            vae,
            norms,
            changepoint,
            remediation]
        writer.writerow(columns)
        yield csvFile.getvalue()
        csvFile.seek(0)
        csvFile.truncate(0)
    yield csvFile.getvalue()