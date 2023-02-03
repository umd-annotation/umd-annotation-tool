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


def export_changepoint_tab(folders, userMap, user):
    
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "timestamp", "impact_scalar", "comment"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)
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


def export_remediation_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "timestamp", "comment"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)

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


def export_norms_tab(folders, userMap, user):
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
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)

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
                        value = userDataFound[key][normKey]
                        if value == 'ahered':
                            value = 'adhere'
                        if value == 'violated':
                            value = 'violate'
                        if value == 'adhered_violated':
                            columns = [
                                key,
                                videoname,
                                f'{videoname}_{t["id"]:04}',
                                normKey,
                                'adhere',
                            ]
                            writer.writerow(columns)
                            columns = [
                                key,
                                videoname,
                                f'{videoname}_{t["id"]:04}',
                                normKey,
                                'violate',
                            ]
                            writer.writerow(columns)
                        else:
                            columns = [
                                key,
                                videoname,
                                f'{videoname}_{t["id"]:04}',
                                normKey,
                                value,
                            ]
                            writer.writerow(columns)

                        
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()


def export_valence_tab(folders, userMap, user):
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
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)

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


def export_segment_tab(folders, userMap, user):
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
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)

        for t in tracks:
            start = t['begin'] * (1 / fps)
            end = t['end'] * (1 / fps)
            columns = [videoname, f'{videoname}_{t["id"]:04}', start, end]
            writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()


def export_emotions_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["user_id", "file_id", "segment_id", "emotion", "multi_speaker"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)

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


def export_session_info_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["session_id", "language", "condition", "fle_id", "sme_id", 'recording_date', 'recording_time'])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        name = videoname.replace('Video', '').replace('.mp4', '')
        splits = name.split('_')
        session_id = name
        language = ''
        condition = ''
        scenario = ''
        fle_id = ''
        fme_id = ''
        recording_date = ''
        recording_time = ''
        if len(splits) > 5:
            language = splits[0]
            condition = splits[1]
            scenario = splits[2]
            fle_id = splits[3]
            sme_id = splits[4]
            recording_date = splits[5]
            session_id = f'{language}_{condition}_{scenario}_{fle_id}_{sme_id}_{recording_date}'

        columns = [session_id, language, condition, scenario, fle_id, sme_id, recording_date, recording_time]
        writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def export_file_info_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["session_id", "file_uid", "type", "length", "source"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        length = folder['meta']['ffprobe_info']['duration']
        name = videoname.replace('Video', '').replace('.mp4', '')
        splits = name.split('_')
        session_id = name
        language = ''
        condition = ''
        scenario = ''
        fle_id = ''
        fme_id = ''
        recording_date = ''
        type = ''
        if len(splits) > 5:
            language = splits[0]
            condition = splits[1]
            scenario = splits[2]
            fle_id = splits[3]
            sme_id = splits[4]
            recording_date = splits[5]
            if len(splits) > 6:
                typebase = splits[6]
                type = typebase.split('-')[0]
            session_id = f'{language}_{condition}_{scenario}_{fle_id}_{sme_id}_{recording_date}'

        columns = [session_id, name, 'video', length, type]
        writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def export_system_input(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["file_id"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        length = folder['meta']['ffprobe_info']['duration']
        name = videoname.replace('Video', '').replace('.mp4', '')
        columns = [name]
        writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def export_versions_per_file(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar="'")
    writer.writerow(["file_id", "emotions_count", "valence_arousal_count", "norms_count", "changepoint_count"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = folder['name']
        fps = folder['meta']['fps']
        name = videoname.replace('Video', '').replace('.mp4', '')
        tracks = crud_annotation.TrackItem().list(folder)
        change_point_count = 0
        emotions_count = 0
        norms_count = 0
        valence_arousal_count = 0
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
        writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def generate_tab(folders, userMap, user, type):
    def downloadGenerator():
        if type == 'segment':
            for data in export_segment_tab(folders, userMap, user):
                yield data
        if type == 'valence':
            for data in export_valence_tab(folders, userMap, user):
                yield data
        if type == 'emotions':
            for data in export_emotions_tab(folders, userMap, user):
                yield data
        if type == 'norms':
            for data in export_norms_tab(folders, userMap, user):
                yield data
        if type == 'changepoint':
            for data in export_changepoint_tab(folders, userMap, user):
                yield data
        if type == 'remediation':
            for data in export_remediation_tab(folders, userMap, user):
                yield data
        if type == 'session_info':
            for data in export_session_info_tab(folders, userMap, user):
                yield data
        if type == 'file_info':
            for data in export_file_info_tab(folders, userMap, user):
                yield data
        if type == 'system_input':
            for data in export_system_input(folders, userMap, user):
                yield data
        if type == 'versions_per_file':
            for data in export_versions_per_file(folders, userMap, user):
                yield data
    return downloadGenerator

def convert_to_zips(folders, userMap, user,):
    def stream():
        z = ziputil.ZipGenerator()            
        zip_path = './'

        seg_gen = generate_tab(folders, userMap, user, 'segment')
        for data in z.addFile(seg_gen, Path(f'{zip_path}/docs/segments.tab')):
            yield data
        valence_gen = generate_tab(folders, userMap, user, 'valence')
        for data in z.addFile(valence_gen, Path(f'{zip_path}/data/valence.tab')):
            yield data
        emotion_gen = generate_tab(folders, userMap, user, 'emotions')
        for data in z.addFile(emotion_gen, Path(f'{zip_path}/data/emotions.tab')):
            yield data
        norm_gen = generate_tab(folders, userMap, user, 'norms')
        for data in z.addFile(norm_gen, Path(f'{zip_path}/data/norms.tab')):
            yield data
        norm_gen = generate_tab(folders, userMap, user, 'changepoint')
        for data in z.addFile(norm_gen, Path(f'{zip_path}/data/changepoint.tab')):
            yield data
        norm_gen = generate_tab(folders, userMap, user, 'remediation')
        for data in z.addFile(norm_gen, Path(f'{zip_path}/data/remediation.tab')):
            yield data
        session_gen = generate_tab(folders, userMap, user, 'session_info')
        for data in z.addFile(session_gen, Path(f'{zip_path}/docs/session_info.tab')):
            yield data
        file_info_gen = generate_tab(folders, userMap, user, 'file_info')
        for data in z.addFile(file_info_gen, Path(f'{zip_path}/docs/file_info.tab')):
            yield data
        system_input_gen = generate_tab(folders, userMap, user, 'system_input')
        for data in z.addFile(system_input_gen, Path(f'{zip_path}/index_files/system_input.index.tab')):
            yield data
        version_per_file_gen = generate_tab(folders, userMap, user, 'versions_per_file')
        for data in z.addFile(version_per_file_gen, Path(f'{zip_path}/docs/versions_per_file.tab')):
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
            "SCENARIO",
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
        LC = 'missing'
        CONDITION = ''
        SCENARIO = ''
        FLE = ''
        SME = ''
        DATE = ''
        PERSON = ''
        PERSPECTIVE = ''
        splits = name.split('_')
        if len(splits) > 6:
            LC = splits[0]
            CONDITION = splits[1]
            SCENARIO = splits[2]
            FLE = splits[3]
            SME = splits[4]
            DATE = splits[5]
            PERSON = splits[6]
            if '-' in PERSON:
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