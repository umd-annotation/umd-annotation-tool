# UMD Annotation Tool

UMD Annotation Tool is a web application for annotation of videos and recording specific annotations relating to linguistic information.

## Getting started

Within the root directory run:
cp the '.env.default' and rename it to '.env'
`docker-compose build`
`docker-compose up`
This will build and bring up the application locally.
The webserver will be located at http://localhost:8010
The girder interface will be located at http://localhost:8010/girder
The girder API will be located at http://localhost:8010/girder/api/v1

## Architecture

### Client

Folder: ./client

Client is based on a fork of the DIVE Web Interface for the Girder version.  For this project it was easier to manipulate the current DIVE interface instead of making it a plugin and trying to import it. 

To develop the client interface:
``` bash
# install dependencies
yarn

# run development server
yarn serve

```

### Backend

Folder: ./server

The backend system copies the existing DIVE Repo and install the DIVE Plugin while removing the extra Bucket_Notifications and RabbitMQ plugins.
It then installs the UMD plugin on top of the DIVE plugin.

The UMD Plugin is separted into:

#### UMD_server

Contains a folder for each different endpoint.
I.E - '/UMD_dataset'
Each root endpoint will have several GET/POST/DELETE/PUT endpoints which can be found using the swagger API (http://localhost:8010/girder/api/v1).

#### UMD_utils

Will contain common function and models for specialized data structures if they are needed for the project
### UMD_tasks

Longer running tasks are implemented in a worker plugin.  Essentially anything that can't be completed in a request thread within 2 seconds will be a task.

### Production Deployment (using Traefik SSL)

Ensure that the default passwords are all changed in the '.env' file
Run the following command.  Use the scaling if you are going to support multiple users and multiple requests.  The `--scale girder=4` is not required

`docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale girder=4`

### Production Deployment (using locally signed certificate)

Create a directory in `./docker` called `certs` and place the certificate and key file in there.

Read the './docker/dynamic.local.https.yml' configuration file and replace the `certFile` and `keyFile` names with your certificate and key.

Run the command:

`docker-compose -f docker-compose.yml -f docker-compose.local.https.yml up`





