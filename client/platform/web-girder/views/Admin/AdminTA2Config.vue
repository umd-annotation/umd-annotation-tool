<script lang="ts">
import { defineComponent, ref, onMounted } from '@vue/composition-api';
import { getUMDTA2Config, putUMDTA2Config, TA2Config } from 'platform/web-girder/api/UMD.service';

export default defineComponent({
  name: 'AdminTA2Config',
  setup() {
    const normMap = ref<TA2Config['normMap']>([]);
    const errorMessage = ref<string | null>(null);

    const fetchConfig = async () => {
      try {
        const data = await getUMDTA2Config();
        normMap.value = data.normMap;
      } catch (error) {
        console.error(error);
        errorMessage.value = 'Failed to load configuration.';
      }
    };

    const handleFileUpload = async (file?: File) => {
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const config: TA2Config = JSON.parse(event.target?.result as string);
          await putUMDTA2Config(config);
          await fetchConfig();
        } catch (error) {
          console.error(error);
          errorMessage.value = 'Invalid JSON file or upload failed.';
        }
      };
      reader.readAsText(file);
    };

    const downloadConfig = () => {
      const json = JSON.stringify({ normMap: normMap.value }, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'TA2ConfigNormMap.json';
      a.click();
      URL.revokeObjectURL(url);
    };

    onMounted(() => {
      fetchConfig();
    });

    return {
      normMap,
      errorMessage,
      handleFileUpload,
      downloadConfig,
    };
  },
});
</script>

<template>
  <v-container>
    <v-card class="mt-5">
      <v-card-title>TA2 Configuration</v-card-title>
      <v-card-subtitle>
        Manage and view the TA2 normalization map configuration.
      </v-card-subtitle>
      <v-card-text>
        <v-alert
          v-if="errorMessage"
          type="error"
          dismissible
          @click:close="errorMessage = null"
        >
          {{ errorMessage }}
        </v-alert>

        <v-data-table
          :headers="[
            { text: 'Name', value: 'named' },
            { text: 'ID', value: 'id' },
            { text: 'Groups', value: 'groups' }
          ]"
          :items="normMap"
          item-value="id"
          :items-per-page="-1"
          hide-default-footer
          class="elevation-1"
        >
          <template #item.groups="{ item }">
            <span
              v-for="group in item.groups"
              :key="group"
              class="mr-2"
            >
              {{ group }}
            </span>
          </template>
        </v-data-table>

        <v-file-input
          label="Upload JSON Configuration"
          accept="application/json"
          class="mt-4"
          @change="handleFileUpload"
        />

        <v-btn
          color="primary"
          class="mt-4"
          @click="downloadConfig"
        >
          Download Current Config
        </v-btn>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<style scoped>
.mt-5 {
  margin-top: 2rem;
}
.mt-4 {
  margin-top: 1.5rem;
}
</style>
