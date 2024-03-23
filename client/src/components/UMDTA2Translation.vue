<script lang="ts">
import {
  defineComponent, PropType, reactive, ref, toRef, watch,
} from '@vue/composition-api';


export interface TA2Translation {
    speaker: string;
    ASRText: string;
    translation: string;
    sourceLanguage: string;
    targetLanguage: string;
}

export default defineComponent({
  name: 'UMDTA2Translation',

  props: {
    data: {
      type: Object as PropType<TA2Translation>,
      required: true,
    },
  },

  setup(props, { emit }) {
    return {
    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col>
        <b>Speaker:</b>
        <span class="ml-2">{{ data.speaker }}</span>
      </v-col>
      <v-col>
        <b>Source:</b>
        <span class="ml-2">{{ data.sourceLanguage }}</span>
      </v-col>
      <v-col>
        <b>Target:</b>
        <span class="ml-2">{{ data.targetLanguage }}</span>
      </v-col>
    </v-row>
    <h3>ASR Text</h3>
    <p>{{ data.ASRText }}</p>
    <h3>Translation</h3>
    <p>{{ data.translation }}</p>
  </div>
</template>

<style lang="scss" scoped>
</style>
