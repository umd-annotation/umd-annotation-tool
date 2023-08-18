import girderRest from 'platform/web-girder/plugins/girder';

const rootAPI = 'UMD_dataset';
function ingestVideo(folderId: string) {
  return girderRest.post(`${rootAPI}/ingest_video/${folderId}`);
}

function updateContainers() {
  return girderRest.post(`${rootAPI}/update_containers`);
}

async function createFilterFolder(folderId: string) {
  const result = await girderRest.post(`${rootAPI}/filter/${folderId}`);
  if (result.status === 200) {
    return result.data;
  }
  return false;
}

export {
  ingestVideo,
  updateContainers,
  createFilterFolder,
};
