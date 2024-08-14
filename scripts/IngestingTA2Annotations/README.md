# Ingesting TA2 Annotations in the UMD Annotation Software

The scripts in this folder are used to process and ingest the data for the TA2 Annotation Software.


## Initialization

Having Python installed and using this folder run `pip install -r requirements.txt` to install the dependencies needed to run the scripts.

## Process Overview

The TA2 Annotations rely on JSONL files from Hololens and other containers that record data about translations and events that occur during a scenario.  These include things like alerts, remediation and automatic speech recognition as well as translation.

These JSONL files need to be converted into a TrackJSON file so that the Annotation Web application can interpret the data and display it to annotators.

The Basic Process is as follows:

1. Process the existing JSONL files by removing base64 encodings and converting the time data into 'turns' and storing them in a Processed JSON file.  This is done by running the **convertFolder.py** script.  After upload these files to a collection on the Annotation Web Application so they can be used in the future to create a TrackJSON file.
2. Load the Videos that are the sources for the JSONL files into a collection on the Annotation Web Application.  These when imported some S3 should automatically be converted to Video Dataset in the system for annotation.
3. Create a Destination Folder where the processed JSON file and the Video will be combined into a final Dataset that can be used for Annotation.
4. Set up all inputs to the **cloneAndConvert.py** script.  These include the source folders for the videos, the source folders for the JSON Processed files and the destination folder for the Cloned datasets.
5. Run the **cloneAndConvert.py** script to create copies of the source videos with embedded translation, alerts and remediation information.  As well as turns for annotation.  The outputs for this script include an 'unmatched.json' file to indicate files that couldn't be matched between the process json files and source videos.  The other output is a 'csv' file that includes links to the different annotation types for all videos that were successfully copied and cloned.


## cloneAndConvert.py Script Details

### cloneAndConvert.py Inputs

- **ADD_CLNG_VIDEOS** - will automatically clone the videos that include CLNG in the title.  These are videos that don’t have a processed JSON to automatically have the translations and turns
- **JSONLSourceFolderId** - A source folder for the JSONL processed files
- **VideoSourceFolderIds** - An array of Ids for where the source video files are.
- **CloneDestinationFolderId** - FolderId for the destination of where you want the cloned datasets to go.  These are the datasets with the translations and turns populated from a matching file in the JSONLSourceFolderId
- **normMap** - A mapping of norms for the Id to a Text representation of the norm

### cloneAndConvert.py Process

1. **Login** - User is prompted for login credentials to the server
2. **Get Source Videos** - It gets processed Videos.  This is searching through all the folders in **VideoSourceFolderIds** for dive datasets that have ‘_THIRD-PERSON.mp4’ in them.  It can returns all of the matching video files.
3. **Group CLNG Videos** - It then takes all of the files from Step 2 and extracts out the videos that have **‘CLNG’** in them so they can be added separately.
4. **Get Existing Videos** - It gets the existing videos from the **CloneDestinationFolderId** and stores them to make sure we don’t overwrite any existing video files.
5. **Gather Processed JSON Files** - It then gets the processed JSON files from **JSONLSourceFolderId**. These are all files that are preprocessed using the convertFolder.py script to remove base64 elements from the JSONL file as well as convert the information into a more turn based JSON file.
6. **Generate Matches** - Takes the processedJSONL files and using the name attempts to match them with a video from the **VideoSourceFolderIds**.  This Will attempt to match, if a match can’t be found it will log it to a unmatching.json file that lists the unmatched JSON file name with the top 5 closest named videos that match it.  This helps if there is a spelling mistake or some kind of other error preventing the matching.
6. **Processing and Cloning** - Now that the data is all gathered and we have matches as well as CLNG videos the program starts making the clones and copying the data over.
    1. If a video that is matched and it already exists in the CloneDestinationFolderId it will skip over the rest of this function.
    2. If not existing it will download and process the JSONProcessed file.  This processing is converting the Turns from the JSONL file to a TrackJSON that can be used to display the data.
    3. The system then creates a clone of the source video in the CloneDestinationFolderId followed up by uploading the newly created TrackJSON to the cloned dataset.
    4. If **ADD_CLNG_VIDEOS** is true the system will then check to see if the file exists and if it doesn’t it will clone the source video file to the destination folder.
       During this process all completed videos are kept track of
7. **Generate Completed CSV** - At the end of processing all the matches and cloned videos the system will generate a CSV that contains the name of the completed videos and a link to the Dataset that can be used to organize annotations.  These include links to each annotation type (ASRMT_Quality, Norms, Remediation)
