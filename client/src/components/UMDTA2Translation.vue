<script lang="ts">
import {
  defineComponent, PropType,
} from '@vue/composition-api';


export interface TA2Translation {
    speaker: string;
    ASRText: string;
    translation: string;
    sourceLanguage: string;
    targetLanguage: string;
    alerts?: { display: string; delayed?: boolean }[];
    rephrase?: { display: string }[];
    rephrase_translation?: {
      translation: string;
      sourceText: string;
    }[];
}

export default defineComponent({
  name: 'UMDTA2Translation',

  props: {
    data: {
      type: Object as PropType<TA2Translation>,
      required: true,
    },
  },

  setup() {
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
    <h3 v-if="data.alerts && data.alerts.length">
      Alerts
    </h3>
    <p v-if="data.alerts">
      <v-row
        v-for="(alert, index) in data.alerts"
        :key="`alert_${index}`"
        class="mx-2"
      >
        <div>
          <b>{{ index+1 }}.</b><span class="ml-2"><v-chip
            v-if="alert.delayed"
            color="warning"
            class="mx-2"
          >Delayed</v-chip>{{ alert.display }}</span>
        </div>
      </v-row>
    </p>
    <h3 v-if="data.rephrase && data.rephrase.length && !(data.rephrase_translation && data.rephrase_translation.length)">
      Rephrase
    </h3>
    <p v-if="data.rephrase && data.rephrase.length && !(data.rephrase_translation && data.rephrase_translation.length)">
      <v-row
        v-for="(alert, index) in data.rephrase"
        :key="`rephrase_${index}`"
        class="mx-2"
      >
        <div><span class="ml-2">{{ alert.display }}</span></div>
      </v-row>
    </p>
    <h3 v-if="data.rephrase_translation && data.rephrase_translation.length">
      Rephrasing
    </h3>
    <p v-if="data.rephrase_translation && data.rephrase_translation.length">
      <v-row
        v-for="(rephrase, index) in data.rephrase_translation"
        :key="`rephrase_translation_${index}`"
        class="mx-2"
      >
        <v-container class="mx-5">
          <v-row>
            <div
              v-if="data.rephrase && data.rephrase.length"
              class="ml-2"
            >
              <div v-if="data.rephrase.length == 1">
                <b class="mr-2">Rephrased:</b>{{ data.rephrase.map((item) => item.display)[0].replace('Rephrased:', '') }}
              </div>
              <div v-else>
                <b class="mr-2">Rephrased:</b>
                <ul>
                  <li
                    v-for="(item, subindex) in data.rephrase"
                    :key="`rephrase_${subindex}`"
                  >
                    {{ item.display }}
                  </li>
                </ul>
              </div>
            </div>
            <div
              v-else
              class="ml-2"
            >
              <b class="mr-2">Source Text:</b>{{ rephrase.sourceText }}
            </div>
          </v-row>
          <v-row>
            <div class="ml-2">
              <b class="mr-2">Translation:</b>{{ rephrase.translation }}
            </div>
          </v-row>
        </v-container>
      </v-row>
    </p>
  </div>
</template>

<style lang="scss" scoped>
</style>
