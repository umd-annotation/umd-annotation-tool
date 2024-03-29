<template>
  <v-app>
    <router-view />
  </v-app>
</template>

<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { provideApi } from 'dive-common/apispec';
import type { GirderMetadata } from './constants';
import '@fontsource/roboto-condensed';
import {
  getPipelineList,
  runPipeline,
  getTrainingConfigurations,
  runTraining,
  saveMetadata,
  saveAttributes,
  importAnnotationFile,
  loadDetections,
  saveDetections,
  unwrap,
} from './api';
import { openFromDisk } from './utils';

export default defineComponent({
  name: 'App',
  components: {},
  setup(_, { root }) {
    async function loadMetadata(datasetId: string): Promise<GirderMetadata> {
      return root.$store.dispatch('Dataset/load', datasetId);
    }

    root.$store.dispatch('Location/setLocationFromRoute', root.$route);

    provideApi({
      getPipelineList: unwrap(getPipelineList),
      runPipeline: unwrap(runPipeline),
      getTrainingConfigurations: unwrap(getTrainingConfigurations),
      runTraining: unwrap(runTraining),
      loadDetections,
      saveDetections: unwrap(saveDetections),
      saveMetadata: unwrap(saveMetadata),
      saveAttributes: unwrap(saveAttributes),
      loadMetadata,
      openFromDisk,
      importAnnotationFile,
    });
  },
});
</script>

<style lang="scss">
html {
  overflow-y: auto;
}

.text-xs-center {
  text-align: center !important;
}
@font-face {
  font-family: "Noto Color Emoji";
  src: local("NotoColor"),
   url(../../public/fonts/NotoColor/NotoColorEmoji-Regular.ttf) format("truetype");
}

</style>
