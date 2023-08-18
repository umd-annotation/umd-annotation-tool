<script >
import Vue from 'vue';
import { mixins } from '@girder/components/src';
import { createFilterFolder } from 'platform/web-girder/api/UMD.service';
import { openFromDisk } from '../utils';

export default Vue.extend({
  name: 'FilterImport',
  mixins: [mixins.fileUploader, mixins.sizeFormatter],
  inject: ['girderRest'],
  props: {
    id: {
      type: String,
      default: '',
    },
    dataType: {
      type: String,
      default: 'xls',
    },
    blockOnUnsaved: {
      type: Boolean,
      default: false,
    },
    buttonOptions: {
      type: Object,
      default: () => ({}),
    },
    menuOptions: {
      type: Object,
      default: () => ({}),
    },
    disabled: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      preUploadErrorMessage: null,
      currentFile: null,
      createdFolder: null,
    };
  },
  computed: {
    progress() {
      const { totalProgress, totalSize } = this;
      if (totalSize !== 0) {
        return {
          totalProgress,
          totalSize,
        };
      }
      return {
        totalProgress: 0,
        totalSize: 0,
      };
    },
  },
  methods: {
    async openUpload() {
      const ret = await openFromDisk('xls');
      if (!ret.canceled) {
        if (ret.fileList?.length) {
          let folder;
          if (this.dataType === 'xls') {
            folder = await createFilterFolder(this.id);
          }
          if (folder) {
            folder._modelType = 'folder';
            this.createdFolder = folder._id;
            this.startUpload(ret.fileList[0], folder);
          }
        }
      }
    },
    async startUpload(file, folder) {
      const fileData = {
        file,
        status: 'pending',
        progress: {
          indeterminate: false,
          current: 0,
          size: file.size,
        },
        upload: null,
        result: null,
      };
      this.currentFile = fileData;
      this.setFiles([fileData]);
      // Upload Mixin function to start uploading
      await this.start({
        dest: folder,
      });
    },
  },
});
</script>

<template>
  <v-tooltip
    open-delay="200"
    bottom
    max-width="200"
  >
    <template #activator="{ on }">
      <div v-on="on">
        <v-btn
          class="ma-0"
          text
          small
          :disabled="disabled !== ''"
          v-bind="buttonOptions"
          @click="openUpload"
        >
          <v-icon color="accent">
            mdi-application-import
          </v-icon>
          <span
            v-show="!$vuetify.breakpoint.mdAndDown || buttonOptions.block"
            class="pl-1"
          >
            Import Filter
          </span>
          <v-icon color="accent">
            mdi-filter
          </v-icon>

          <span
            v-if="progress.totalSize !== 0"
          >
            <v-progress-circular
              :value="progress.totalProgress/progress.totalSize*100"
            />
          </span>
        </v-btn>
      </div>
    </template>
    <span v-if="disabled">{{ disabled }}</span>
  </v-tooltip>
</template>

    <style scoped lang="scss">
    </style>
