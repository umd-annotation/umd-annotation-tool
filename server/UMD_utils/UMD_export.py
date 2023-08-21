import csv
import io
import json
import math
from pathlib import Path
import pandas as pd
import re

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
    "None": 'none',
}

normValuesViolate = ['violate', 'violated']
normValuesAdhere = ['adhere', 'adhered']
normValuesAdhereViolate = ['adhere_violate', 'adhered_violated']
normValuesNone = ['noann', 'EMPTY_NA']
normViolate = 'violate'
normAdhere = 'adhere'
NormAdhereViolate = 'adhere_violate'
normNone = 'EMPTY_NA'

TrackAttributeExists = ['_Arousal', '_Valence', '_Norms', '_Emotions']
FrameAttributeExists = ['_Impact', '_RemediationComment']

removed_elements = ['Video ', '.mp4', '-TIGHT', '-MID', '-WIDE']

def process_video_name(name):
    for remove in removed_elements:
        name = name.replace(remove, '')
    return name


def bin_value(value):
    return math.floor((value - 1) / 200) + 1

def bin_changepoint(value):
    return math.floor((value - 1) / 1000) + 1

def annotations_exists(tracks):
    for t in tracks:
        if 'features' in t.keys():
            features = t['features']
            attributes = t['attributes']
            for key in attributes.keys():
                if any(check in key for check in TrackAttributeExists):
                    return True
            for feature in features:
                if 'attributes' in feature.keys():
                    frameAttributes = feature['attributes']
                    for frameAttribute in frameAttributes.keys():
                        if any(check in frameAttribute for check in FrameAttributeExists):
                            return True
    return False


def export_changepoint_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["user_id", "file_id", "timestamp", "impact_scalar", "comment"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)
        minus_frames = 0
        for t in tracks:
            if t['id'] == 0 and t['begin'] > 0:
                minus_frames = t['begin']
            if 'features' in t.keys():
                features = t['features']
                userDataFound = {}
                for feature in features:
                    if 'attributes' in feature.keys():
                        attributes = feature['attributes']
                        for key in attributes.keys():
                            if '_ImpactV2.0' in key:
                                login = key.replace('_ImpactV2.0', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Impact'] = bin_changepoint(attributes[key])
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * (feature['frame'] - minus_frames)
                            elif '_Impact' in key:
                                login = key.replace('_Impact', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Impact'] = bin_changepoint(attributes[key] * 1000)
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * (feature['frame'] - minus_frames)
                            if '_Comment' in key:
                                login = key.replace('_Comment', '')
                                mapped = login
                                if mapped not in userDataFound.keys():
                                    userDataFound[mapped] = {}
                                userDataFound[mapped]['Comment'] = str(attributes[key])
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * (feature['frame'] - minus_frames)

                for key in userDataFound.keys():
                    userId = userMap[key]['uid']
                    columns = [
                        userId,
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
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["user_id", "file_id", "timestamp", "comment"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)
        minus_frames = 0
        for t in tracks:
            if t['id'] == 0 and t['begin'] > 0:
                minus_frames = t['begin']
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
                                userDataFound[mapped]['Timestamp'] = (1 / fps) * (feature['frame'] - minus_frames)

                for key in userDataFound.keys():
                    userId = userMap[key]['uid']
                    columns = [
                        userId,
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
        videoname = process_video_name(folder['name'])
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
                        userId = userMap[key]['uid']
                        if value in normValuesAdhere:
                            value = normAdhere
                        if value in normValuesViolate:
                            value = normViolate
                        if value in normValuesAdhereViolate:
                            columns = [
                                userId,
                                videoname,
                                f'{videoname}_{t["id"]:04}',
                                normKey,
                                normAdhere,
                            ]
                            writer.writerow(columns)
                            columns = [
                                userId,
                                videoname,
                                f'{videoname}_{t["id"]:04}',
                                normKey,
                                normViolate,
                            ]
                            writer.writerow(columns)
                        else:
                            if value in normValuesNone:
                                value = normNone
                            columns = [
                                userId,
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
        videoname = process_video_name(folder['name'])
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
                    userId = userMap[key]['uid']
                    columns = [
                        userId,
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
        name = process_video_name(videoname)
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)
        splits = name.split('_')
        session_id = name
        language = ''
        condition = ''
        scenario = ''
        fle_id = ''
        fme_id = ''
        recording_date = ''
        recording_time = ''
        typebase = ''
        if len(splits) > 5:
            language = splits[0]
            condition = splits[1]
            scenario = splits[2]
            fle_id = splits[3]
            sme_id = splits[4]
            recording_date = splits[5]
            if len(splits) > 6:
                typebase = splits[6]

            updatedName = f'{language}_{condition}_{scenario}_{fle_id}_{sme_id}_{recording_date}_{typebase}'
        if annotations_exists(tracks):
            tracks.rewind()
            minus_frames = 0
            for t in tracks:
                if t['id'] == 0 and t['begin'] > 0:
                    minus_frames = t['begin']
                start = (t['begin'] - minus_frames) * (1 / fps)
                end = (t['end'] - minus_frames) * (1 / fps)
                columns = [updatedName, f'{updatedName}_{t["id"]:04}', start, end]
                writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()


def export_emotions_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["user_id", "file_id", "segment_id", "emotion", "multi_speaker"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        fps = folder['meta']['fps']
        tracks = crud_annotation.TrackItem().list(folder)
        name = videoname

        for t in tracks:
            if 'attributes' in t.keys():
                attributes = t['attributes']
                userDataFound = {}
                emotionIsNone = False
                for key in attributes.keys():
                    if '_Emotions' in key:
                        login = key.replace('_Emotions', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        base = ','.join(attributes[key].split('_'))
                        if base == 'No emotions':
                            base = 'none'
                        userDataFound[mapped]['Emotions'] = base
                    if '_MultiSpeaker' in key:
                        login = key.replace('_MultiSpeaker', '')
                        mapped = login
                        if mapped not in userDataFound.keys():
                            userDataFound[mapped] = {}
                        userDataFound[mapped]['MultiSpeaker'] = attributes[key]
                for key in userDataFound.keys():
                    userId = userMap[key]['uid']
                    multiSpeaker = userDataFound[key]['MultiSpeaker']
                    if userDataFound[key]["Emotions"] == 'none':
                        multiSpeaker = 'EMPTY_NA'
                    columns = [
                        userId,
                        name,
                        f'{name}_{t["id"]:04}',
                        f'{userDataFound[key]["Emotions"].lower()}',
                        multiSpeaker,
                    ]
                    writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()


def export_session_info_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["session_id", "language", "condition", "scenario", "fle_id", "sme_id", 'recording_date', 'recording_time'])
    existing_session = []
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        name = videoname
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

        if session_id in existing_session:
            continue
        columns = [session_id, language, condition, scenario, fle_id, sme_id, recording_date, recording_time]
        writer.writerow(columns)
        existing_session.append(session_id)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def export_file_info_tab(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["session_id", "file_uid", "type", "length", "source"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        length = folder['meta']['ffprobe_info']['duration']
        name = videoname
        splits = name.split('_')
        session_id = name
        language = ''
        condition = ''
        scenario = ''
        fle_id = ''
        fme_id = ''
        recording_date = ''
        type = ''
        tracks = crud_annotation.TrackItem().list(folder)
        if (annotations_exists(tracks)):
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
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["file_id"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        length = folder['meta']['ffprobe_info']['duration']
        name = videoname
        columns = [name]
        writer.writerow(columns)
    yield csvFile.getvalue()
    csvFile.seek(0)
    csvFile.truncate(0)
    yield csvFile.getvalue()

def export_versions_per_file(folders, userMap, user):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t', quotechar='"')
    writer.writerow(["file_id", "emotions_count", "valence_arousal_count", "norms_count", "changepoint_count"])
    for folderId in folders:
        folder = Folder().load(folderId, level=AccessType.READ, user=user)
        videoname = process_video_name(folder['name'])
        fps = folder['meta']['fps']
        name = videoname
        tracks = crud_annotation.TrackItem().list(folder)
        change_point_count = 0
        changepointUserDataFound = []
        emotions_count = 0
        emotionsUserDataFound = {}
        norms_count = 0
        normsUserDataFound = {}
        valence_arousal_count = 0
        valenceUserDataFound = {}
        track_length = tracks.count()
        for t in tracks:
            if 'features' in t.keys():
                features = t['features']
                if 'attributes' in t.keys():
                    track_attributes = t['attributes']
                    for key in track_attributes.keys():
                        if '_Emotions' in key:
                            login = key.replace('_Emotions', '')
                            if login not in emotionsUserDataFound.keys():
                                emotionsUserDataFound[login] = 1
                            else:
                                emotionsUserDataFound[login] += 1
                        if '_Valence' in key:
                            login = key.replace('_Valence', '')
                            if login not in valenceUserDataFound.keys():
                                valenceUserDataFound[login] = 1
                            else:
                                valenceUserDataFound[login] += 1
                        if '_Norms' in key:
                            login = key.replace('_Norms', '')
                            if login not in normsUserDataFound.keys():
                                normsUserDataFound[login] = 1
                            else:
                                normsUserDataFound[login] += 1
                        if '_ChangePointComplete' in key:
                            login = key.replace('_Norms', '')
                            if login not in changepointUserDataFound:
                                changepointUserDataFound.append(login)
        # iterate over the user counts and make sure they match the track length
        for login in emotionsUserDataFound.keys():
            if emotionsUserDataFound[login] == track_length:
                emotions_count += 1
        for login in valenceUserDataFound.keys():
            if valenceUserDataFound[login] == track_length:
                valence_arousal_count += 1
        for login in normsUserDataFound.keys():
            if normsUserDataFound[login] == track_length:
                norms_count += 1
        change_point_count = len(changepointUserDataFound)
        if emotions_count + valence_arousal_count + norms_count + change_point_count > 0:
            columns = [name, emotions_count, valence_arousal_count, norms_count, change_point_count]
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
        if type == 'userMap':
            for data in export_user_map(userMap):
                yield data
    return downloadGenerator

def convert_to_zips(folders, userMap, user):
    def stream():
        z = ziputil.ZipGenerator()            
        zip_path = './'

        seg_gen = generate_tab(folders, userMap, user, 'segment')
        for data in z.addFile(seg_gen, Path(f'{zip_path}/docs/segments.tab')):
            yield data
        valence_gen = generate_tab(folders, userMap, user, 'valence')
        for data in z.addFile(valence_gen, Path(f'{zip_path}/data/valence_arousal.tab')):
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
        userMap_file = generate_tab(folders, userMap, user, 'userMap')
        for data in z.addFile(userMap_file, Path(f'{zip_path}/userMap.tab')):
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
        name = folder['name'].replace('.mp4', '').replace('Video ', '')
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


def export_user_map(userMap):
    csvFile = io.StringIO()
    writer = csv.writer(csvFile, delimiter='\t')
    writer.writerow(
        [
            "uid",
            "login",
            "email",
            "first",
            "last",
            "login",
            'girderId'
        ]
    )
    for key in userMap.keys():
        user = userMap[key]
        columns = [ 
            user['uid'],
            user['login'],
            user['email'],
            user['first'],
            user['last'],
            user['login'],
            user['girderId'],
        ]
        writer.writerow(columns)
        yield csvFile.getvalue()
        csvFile.seek(0)
        csvFile.truncate(0)
    yield csvFile.getvalue()


def create_user_filter_map(excel_file):
    # Read the Excel file
    try:
        df = pd.read_excel(excel_file, sheet_name='UserMap')
    except pd.errors.EmptyDataError:
        print("The UserMap sheet is empty.")
        return
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return
    expected_columns = ['Name', 'UserName', 'Email', 'GirderId']
    if not all(col in df.columns for col in expected_columns):
        print("The sheet UserMap does not contain all the expected columns.")
        return

    # Create a dictionary to store user data
    users = {}

    # Iterate through the rows and create a dictionary for each user
    for _, row in df.iterrows():
        user_data = {
            'Name': row['Name'],
            'UserName': row['UserName'],
            'Email': row['Email'],
            'GirderId': row['GirderId']
        }
        users[user_data['Name']] = user_data
    return users

def read_sheet(excel_file, sheet_name):
        # Name of the sheet you want to extract data from
    sheet_name = 'FLE VAE'

    # Read the Excel file
    try:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=1)  # Skip the first row (header) in the data
    except pd.errors.EmptyDataError:
        print(f"The '{sheet_name}' sheet is empty.")
        return
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return

    # Verify that the expected columns exist in the sheet
    expected_columns = ['File Name', 'Link', 'Annotator', 'Status', 'Completion Date']
    if not all(col in df.columns for col in expected_columns):
        print(f"The sheet '{sheet_name}' does not contain all the expected columns.")
        return
    df = df.dropna(subset=['File Name', 'Link'])

    # Create a dictionary to store the desired data
    data_dict = {}

    # Iterate through the rows and extract the desired fields
    for _, row in df.iterrows():
        file_name = row['File Name']
        link = row['Link']
        annotator = row['Annotator']
        status = row['Status']
        completion_date = row['Completion Date']
        # Extract GirderId from the link
        girder_id_match = re.search(r'/([a-f0-9\-]+)\?', link)
        girder_id = girder_id_match.group(1) if girder_id_match else None

        # Create a dictionary for the current row
        row_data = {
            'FileName': file_name,
            'Link': link,
            'GirderId': girder_id,
            'Annotator': annotator,
            'Status': status,
            'Completion Date': completion_date
        }

        # Use the FileName as the dictionary key
        data_dict[girder_id] = row_data

    return data_dict

def create_filter_mapping(excel_file):
    filterMap = {}

    userMap = create_user_filter_map(excel_file)
    print(userMap)
    fle_vae = read_sheet(excel_file, 'FLE VAUE')
    fle_social_norms = read_sheet(excel_file, 'FLE Social Norms')
    change_point = read_sheet(excel_file, 'Changepoint')
    sme_social_norms = read_sheet(excel_file, 'SME Social Norms')

    filterMap['users'] = userMap
    filterMap['videos'] = {
        'VAE': fle_vae,
        'ChangePoint': change_point,
        'Social Norms': {**fle_social_norms, ** sme_social_norms},
    }
    return filterMap
