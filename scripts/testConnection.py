import girder_client
import json
import click
import requests
import csv
import os


apiURL = "annotation.umd.edu"




def login():
    gc = girder_client.GirderClient(apiURL, port=443, apiRoot='girder/api/v1' )
    gc.authenticate(interactive=True)
    return gc



@click.command(name="cloneAndConvert", help="Load in ")
def run_script():
    response = requests.get('https://annotation.umd.edu')
    print(response.status_code)



    # gc = login()
    # video_map = get_processVideos(gc)
    # print(video_map)


if __name__ == '__main__':
    run_script()


