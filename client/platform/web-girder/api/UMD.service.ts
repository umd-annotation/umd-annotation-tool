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

type TA2NormMap = { named: string; id: number; groups: string[] };
export interface TA2Config {
  normMap: TA2NormMap[];
}
const configAPI = 'UMD_configuration';
async function getUMDTA2Config() {
  const result = await girderRest.get<TA2Config>(`${configAPI}/TA2_config`);
  return result.data;
}

async function putUMDTA2Config(config: TA2Config) {
  const result = await girderRest.put(`${configAPI}/TA2_config`, config);
  return result;
}

export {
  ingestVideo,
  updateContainers,
  createFilterFolder,
  getUMDTA2Config,
  putUMDTA2Config,
};
