import os
import click
import json
import cv2
import math


def video_info(videofilename):
    cv2video = cv2.VideoCapture(videofilename)
    height = cv2video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = cv2video.get(cv2.CAP_PROP_FRAME_WIDTH)
    print("Video Dimension: height:{} width:{}".format(height, width))

    framecount = cv2video.get(cv2.CAP_PROP_FRAME_COUNT)
    frames_per_sec = cv2video.get(cv2.CAP_PROP_FPS)
    print("Video duration (sec):", framecount / frames_per_sec)

    return {
        "height": height,
        "width": width,
        "framecount": framecount,
        "frames_per_sec": frames_per_sec,
    }


def generate_tracks(videoinfo):
    # skip first 5 seconds
    fps = videoinfo["frames_per_sec"]
    width = videoinfo["width"]
    height = videoinfo["height"]
    start = fps * 5.0
    framecount = videoinfo["framecount"]
    current_frame = start
    tracks = {}
    track_count = 0
    while current_frame < framecount:
        end = min(framecount, current_frame + (15.0 * fps))
        tracks[track_count] = {
            "begin": current_frame,
            "end": end,
            "confidencePairs": [["segment", 1.0]],
            "attributes": {},
            "id": track_count,
            "features": [
                {
                    "bounds": [0, 0, width, height],
                    "frame": current_frame,
                    "interpolate": True,
                    "keyframe": True,
                },
                {
                    "bounds": [0, 0, width, height],
                    "frame": end,
                    "interpolate": True,
                    "keyframe": True,
                },
            ],
            "meta": {},
        }
        track_count += 1
        current_frame = current_frame + (15.0 * fps)
    return tracks


@click.command(
    name="Generate Tracks",
    help="Takes a video and meta config and generates a track file",
)
@click.argument("video")
@click.argument("destfile")
def load_data(video, destfile):
    videoinfo = video_info(video)
    tracks = generate_tracks(videoinfo)
    with open(f"{destfile}.json", "w") as outfile:
        outfile.write(json.dumps({"tracks": tracks, "groups": {}, "version": 2}))


if __name__ == "__main__":
    load_data()
