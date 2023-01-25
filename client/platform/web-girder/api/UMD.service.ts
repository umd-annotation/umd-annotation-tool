import girderRest from 'platform/web-girder/plugins/girder';

const rootAPI = 'UMD_dataset';
function ingestVideo(folderId: string) {
  return girderRest.post(`${rootAPI}/ingest_video/${folderId}`);
}

function updateContainers() {
  return girderRest.post(`${rootAPI}/update_containers`);
}


export {
  ingestVideo,
  updateContainers,
};
