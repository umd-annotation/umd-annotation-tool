import csv
import io
import json
from pathlib import Path

from dive_server import crud_annotation
from girder.utility import ziputil


def export_segment_tab(tracks, folderId, fps, userId):
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
        start = t['begin'] * fps
        end = t['end'] * fps
        columns = [folderId, f'{folderId}_{t["id"]:04}', start, end]
        writer.writerow(columns)
        yield csvFile.getvalue()
        csvFile.seek(0)
        csvFile.truncate(0)
    yield csvFile.getvalue()


def generate_tab(tracks, folderId, fps, userId, type):
    def downloadGenerator():
        if type == 'segment':
            for data in export_segment_tab(tracks, folderId, fps, userId):
                yield data

    return downloadGenerator


def convert_to_zips(tracks, folder, fps, userId):
    folderId = folder['_id']

    def makeSegmentGen(tracks, folderId, fps, userId):
        segment_gen = generate_tab(tracks, folderId, fps, userId, 'segment')
        return segment_gen

    def stream():
        z = ziputil.ZipGenerator()
        zip_path = "./"

        def makeDiveJson():
            """Include DIVE JSON output annotation file"""
            annotations = crud_annotation.get_annotations(folder)
            print(annotations)
            yield json.dumps(annotations)

        for data in z.addFile(makeDiveJson, Path(f'{zip_path}annotations.json')):
            yield data
        seg_gen = makeSegmentGen(tracks, folderId, fps, userId)
        for data in z.addFile(seg_gen, Path(f'{zip_path}segment_tab.tab')):
            yield data
        yield z.footer()

    return stream
