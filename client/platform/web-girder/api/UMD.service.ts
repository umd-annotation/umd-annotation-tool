import girderRest from 'platform/web-girder/plugins/girder';

const rootAPI = 'UMD_dataset';
function ingestVideo(folderId: string) {
  return girderRest.post(`${rootAPI}/ingest_video/${folderId}`);
}

export {
  // eslint-disable-next-line import/prefer-default-export
  ingestVideo,
};
