<script lang="ts">
import {
  computed, defineComponent, ref, onBeforeUnmount, onMounted,
} from '@vue/composition-api';
import {
  GirderFileManager, getLocationType, GirderModel,
} from '@girder/components/src';
import { itemsPerPageOptions } from 'dive-common/constants';
import { clientSettings } from 'dive-common/store/settings';
import { getManagerGroup, getUri } from 'platform/web-girder/api';
import { useGirderRest } from 'platform/web-girder/plugins/girder';
import { useStore, LocationType, RootlessLocationType } from '../store/types';
import Upload from './Upload.vue';
import eventBus from '../eventBus';

export default defineComponent({
  components: {
    GirderFileManager,
    Upload,
  },

  setup() {
    const fileManager = ref();
    const store = useStore();
    const restClient = useGirderRest();
    const uploading = ref(false);
    const uploaderDialog = ref(false);
    const locationStore = store.state.Location;
    const { getters } = store;

    function setLocation(location: LocationType) {
      store.dispatch('Location/setRouteFromLocation', location);
    }

    function handleNotification() {
      fileManager.value.$refs.girderBrowser.refresh();
    }

    function updateUploading(newval: boolean) {
      uploading.value = newval;
      if (!newval) {
        fileManager.value.$refs.girderBrowser.refresh();
        uploaderDialog.value = false;
      }
    }

    const isManager = ref(false);

    const checkUser = async () => {
      const managerGroup = await getManagerGroup();
      const user = await restClient.fetchUser();
      if (managerGroup.data.length && user.groups.includes(managerGroup.data[0]._id)) {
        isManager.value = true;
      }
    };

    onMounted(() => checkUser());

    function isAnnotationFolder(item: GirderModel) {
      return item._modelType === 'folder' && item.meta.annotate && item.meta.UMDAnnotation !== 'TA2';
    }
    function isTA2Folder(item: GirderModel) {
      return item._modelType === 'folder' && item.meta.annotate && item.meta.UMDAnnotation === 'TA2';
    }

    const shouldShowUpload = computed(() => (
      locationStore.location
      && !getters['Location/locationIsViameFolder']
      && getLocationType(locationStore.location) === 'folder'
      && !locationStore.selected.length
    ));

    eventBus.$on('refresh-data-browser', handleNotification);
    onBeforeUnmount(() => {
      eventBus.$off('refresh-data-browser', handleNotification);
    });

    const copyLink = (id: string, mode: string) => {
      const text = `${window.location.origin}/#/viewer/${id}?mode=${mode}`;
      navigator.clipboard.writeText(text);
    };

    const exportLinks = () => {
      const id = locationStore.location && (locationStore.location as RootlessLocationType)._id;
      const url = `UMD_dataset/links/${id}`;
      const link = getUri({ url });
      window.location.assign(link);
    };

    const exportAnnotations = () => {
      const id = locationStore.location && (locationStore.location as RootlessLocationType)._id;
      const url = `UMD_dataset/recursive_export/${id}`;
      const link = getUri({ url });
      window.location.assign(link);
    };

    return {
      fileManager,
      locationStore,
      getters,
      shouldShowUpload,
      uploaderDialog,
      uploading,
      clientSettings,
      itemsPerPageOptions,
      /* methods */
      isAnnotationFolder,
      handleNotification,
      setLocation,
      updateUploading,
      copyLink,
      exportLinks,
      exportAnnotations,
      isTA2Folder,
      isManager,
    };
  },
});
</script>


<template>
  <GirderFileManager
    ref="fileManager"
    v-model="locationStore.selected"
    :selectable="!getters['Location/locationIsViameFolder']"
    :new-folder-enabled="
      !locationStore.selected.length && !getters['Location/locationIsViameFolder']
    "
    :location="locationStore.location"
    :items-per-page.sync="clientSettings.rowsPerPage"
    :items-per-page-options="itemsPerPageOptions"
    @update:location="setLocation($event)"
  >
    <template #headerwidget>
      <v-dialog
        v-if="shouldShowUpload"
        v-model="uploaderDialog"
        max-width="800px"
        :persistent="uploading"
      >
        <template #activator="{on}">
          <v-btn
            class="ma-0"
            text
            small
            v-on="on"
          >
            <v-icon
              left
              color="accent"
            >
              mdi-file-upload
            </v-icon>
            Upload
          </v-btn>
        </template>
        <Upload
          :location="locationStore.location"
          @update:uploading="updateUploading"
          @close="uploaderDialog = false"
        />
      </v-dialog>
      <!-- <v-btn
        v-if="locationStore &&
          locationStore.location && locationStore.location._modelType === 'folder'"
        class="ma-0"
        text
        small
        @click="exportLinks()"
      >
        <v-icon
          left
          color="accent"
        >
          mdi-file-delimited
        </v-icon>
        Export Links
      </v-btn>
      <v-btn
        v-if="locationStore &&
          locationStore.location && locationStore.location._modelType === 'folder'"
        class="ma-0"
        text
        small
        @click="exportAnnotations()"
      >
        <v-icon
          left
          color="accent"
        >
          mdi-file-delimited
        </v-icon>
        Export Annotations
      </v-btn> -->
    </template>
    <template #row="{item}">
      <span>{{ item.name }}</span>
      <v-icon
        v-if="getters['Jobs/datasetRunningState'](item._id)"
        color="warning"
        class="rotate"
      >
        mdi-autorenew
      </v-icon>
      <v-btn
        v-if="isAnnotationFolder(item)"
        class="ml-2"
        x-small
        color="primary"
        depressed
        :to="{ name: 'viewer', params: { id: item._id } }"
      >
        Launch Annotator
      </v-btn>
      <v-btn
        v-if="isAnnotationFolder(item)"
        class="ml-2"
        x-small
        color="red"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'VAE' } }"
      >
        V/A/E
        <v-icon
          x-small
          class="ml-2"
          @click.prevent.stop="copyLink(item._id, 'VAE')"
        >
          mdi-content-copy
        </v-icon>
      </v-btn>
      <v-btn
        v-if="isAnnotationFolder(item)"
        class="ml-2"
        x-small
        color="green"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'norms' } }"
      >
        Norms
        <v-icon
          x-small
          class="ml-2"
          @click.prevent.stop="copyLink(item._id, 'norms')"
        >
          mdi-content-copy
        </v-icon>
      </v-btn>
      <v-btn
        v-if="isAnnotationFolder(item)"
        class="ml-2"
        x-small
        color="purple"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'changepoint' } }"
      >
        ChangePoint
        <v-icon
          x-small
          class="ml-2"
          @click.prevent.stop="copyLink(item._id, 'changepoint')"
        >
          mdi-content-copy
        </v-icon>
      </v-btn>
      <v-btn
        v-if="isAnnotationFolder(item)"
        class="ml-2"
        x-small
        color="brown"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'remediation' } }"
      >
        Remediation
        <v-icon
          x-small
          class="ml-2"
          @click.prevent.stop="copyLink(item._id, 'remediation')"
        >
          mdi-content-copy
        </v-icon>
      </v-btn>
      <v-btn
        v-if="isTA2Folder(item) && item.name.includes('CLNG')"
        class="ml-2"
        x-small
        color="primary"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_MTQuality' } }"
      >
        TA2 Translation Quality
      </v-btn>
      <v-btn
        v-if="isTA2Folder(item) && !item.name.includes('CLNG')"
        class="ml-2"
        x-small
        color="primary"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_ASRMTQuality' } }"
      >
        TA2 Translation Quality
      </v-btn>

      <v-btn
        v-if="isTA2Folder(item)"
        class="ml-2"
        x-small
        color="purple"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_Norms' } }"
      >
        TA2 Norms
      </v-btn>
      <v-btn
        v-if="isTA2Folder(item)"
        class="ml-2"
        x-small
        color="orange"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_Remediation' } }"
      >
        TA2 Remediation
      </v-btn>
      <v-btn
        v-if="isTA2Folder(item) && false"
        class="ml-2"
        x-small
        color="primary"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_All' } }"
      >
        TA2 All
      </v-btn>
      <v-btn
        v-if="isTA2Folder(item) && isManager && item.name.includes('CLNG')"
        class="ml-2"
        x-small
        color="cyan"
        depressed
        :to="{ name: 'viewer', params: { id: item._id }, query : { mode: 'TA2Annotation_Creation' } }"
      >
        TA2 Creation
      </v-btn>

      <v-chip
        v-if="(item.foreign_media_id)"
        color="white"
        x-small
        outlined
        disabled
        class="my-0 mx-3"
      >
        cloned
      </v-chip>
      <v-chip
        v-if="(item.meta && item.meta.published)"
        color="green"
        x-small
        outlined
        disabled
        class="my-0 mx-3"
      >
        published
      </v-chip>
    </template>
  </GirderFileManager>
</template>
