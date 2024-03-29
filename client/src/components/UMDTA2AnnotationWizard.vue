<script lang="ts">
import {
  defineComponent, PropType, ref, Ref,
} from '@vue/composition-api';


export type NormsList = 'Admiration' | 'Apology' | 'Criticism' | 'Finalizing Negotiating/Deal' | 'Greeting' | 'Persuasion' | 'Refusing a Request' | 'Request' | 'Taking Leave' | 'Thanks';


export interface TA2NormStatus {
  status: 'adhered' | 'violated';
  remediation: number; //0 -unecessary, 1 recommended, 2 necessary
}

export interface TA2Annotation {
  ASRQuality?: number; //Quality number from 0-3
  MTQuality?: number; // Quality number from 0-3
  AlertsQuality?: number; // Quality number from 0-4
  RephrasingQuality?: number; // Quality number from 0-4
  DelayedRemediation?: boolean;
  Norms?: Record<NormsList, TA2NormStatus>;
}


export default defineComponent({
  name: 'UMDTA2AnnotationWizard',

  components: {
  },

  props: {
    annotations: {
      type: Object as PropType<TA2Annotation>,
      required: true,
    },
  },

  setup(props, { emit }) {
    const annotationState: Ref<'ASRMTQuality' | 'Norms' | 'AlertRephrasing'> = ref('ASRMTQuality');
    const steps = ref(['ASR/Translation Quality', 'Norm Adherence/Violation', 'Remediation Qaulity']);

    const ASRQuality = ref(0);
    const MTQuality = ref(0);
    const AlertsQuality = ref(0);
    const RephrasingQuality = ref(0);
    const DelayedRemediation = ref(false);
    const Norms: Ref<Partial<Record<NormsList, TA2NormStatus>>> = ref({});
    const selectedNorms: Ref<NormsList[]> = ref([]);
    const baseNorms = ref([
      'Admiration',
      'Apology',
      'Criticism',
      'Finalizing Negotiating/Deal',
      'Greeting',
      'Persuasion',
      'Refusing a Request',
      'Request',
      'Taking Leave',
      'Thanks',


    ]);
    return {
      annotationState,
      steps,
      ASRQuality,
      MTQuality,
      Norms,
      baseNorms,
      selectedNorms,
      AlertsQuality,
      RephrasingQuality,
      DelayedRemediation,
    };
  },
});
</script>


<template>
  <v-stepper :items="steps">
    <template v-slot:item.1>
      <v-card
        title="ASR/Translation Quality"
        flat
      >
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-row dense>
              <v-col cols="2">
                ASR Quality
              </v-col>
              <v-col>
                <v-slider
                  v-model="ASRQuality"
                  min="1"
                  max="1000"
                  step="1"
                  dense
                  persistent-hint
                />
              </v-col>
              <v-col cols="1">
                <v-tooltip
                  open-delay="200"
                  left
                  max-width="300"
                >
                  <template #activator="{ on }">
                    <v-icon
                      v-on="on"
                    >
                      mdi-help
                    </v-icon>
                  </template>
                  <p style="font-size:1.4em">
                    Evaluation the ASR Quality
                    <ul>
                      <li>
                        0= Very low quality, inadequate; overall gist of message and details may be very difficult to
                        comprehend without relying on contextual clues.
                      </li>
                      <li>
                        1= Tending toward low quality, but minimally adequate; overall gist of message and most
                        details is comprehensible with some difficulty
                      </li>
                      <li>
                        2= Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing
                        (interpretation) elements but mainly comprehensible
                      </li>
                      <li>
                        3= Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and
                        ceiling condition interpretation).
                      </li>
                    </ul>
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-row dense>
              <v-col cols="2">
                MT Quality
              </v-col>
              <v-col>
                <v-slider
                  v-model="MTQuality"
                  min="1"
                  max="1000"
                  step="1"
                  dense
                  persistent-hint
                />
              </v-col>
              <v-col cols="1">
                <v-tooltip
                  open-delay="200"
                  left
                  max-width="300"
                >
                  <template #activator="{ on }">
                    <v-icon
                      v-on="on"
                    >
                      mdi-help
                    </v-icon>
                  </template>
                  <p style="font-size:1.4em">
                    Evaluation the Machine Translation Quality
                    <ul>
                      <li>
                        0= Very low quality, inadequate; overall gist of message and details may be very difficult to
                        comprehend without relying on contextual clues.
                      </li>
                      <li>
                        1= Tending toward low quality, but minimally adequate; overall gist of message and most
                        details is comprehensible with some difficulty
                      </li>
                      <li>
                        2= Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing
                        (interpretation) elements but mainly comprehensible
                      </li>
                      <li>
                        3= Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and
                        ceiling condition interpretation).
                      </li>
                    </ul>
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-card>
    </template>

    <template v-slot:item.2>
      <v-card
        title="Norm Adherence/Violation"
        flat
      >
        <v-row>
          <v-select
            v-model="selectedNorms"
            label="Norms"
            multiple
            items="baseNorms"
            chips
            clearable
            deletable-chips
          />
        </v-row>
        <v-list>
          <v-list-item
            v-for="(item,key) in Norms"
            :key="key"
          >
            <v-select
              v-if="item && item.status"
              label="status"
              :items="['adhered', 'violated']"
              :value="item?.status"
            />
            <v-select
              v-if="item && item.remediation"
              :disabled="item && item.status === 'adhered'"
              label="status"
              :items="[
                { title: 'Unnecessary', value: 0 },
                { title: 'Recommended', value: 1 },
                { title: 'Necessary', value: 2 },
              ]"
              :value="item?.status"
            />
          </v-list-item>
        </v-list>
      </v-card>
    </template>

    <template v-slot:item.3>
      <v-card
        title="Remediation Quality"
        flat
      >
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-row dense>
              <v-col cols="2">
                Alerts Quality
              </v-col>
              <v-col>
                <v-slider
                  v-model="AlertsQuality"
                  min="0"
                  max="4"
                  step="1"
                  dense
                  persistent-hint
                />
              </v-col>
              <v-col cols="1">
                <v-tooltip
                  open-delay="200"
                  left
                  max-width="300"
                >
                  <template #activator="{ on }">
                    <v-icon
                      v-on="on"
                    >
                      mdi-help
                    </v-icon>
                  </template>
                  <p style="font-size:1.4em">
                    Evaluation the Alerts Quality
                    <ul>
                      <li>
                        0= Alerts have a siginficant negative impact to the dialog by distracting the speaker or are categorically inaccurate
                      </li>
                      <li>
                        1= Alerts have a slight negative impact by distracting the speaker or are slightly inaccurate.
                      </li>
                      <li>
                        1000
                      </li><li>
                        3= Alerts help slightly, lead to a slightly more culturally appropriate utterance.
                      </li>
                      <li>
                        4= Alerts have a significant positive impact on the dialog by generating accruate alerts that lead to significantly improved cultural appropriatenesss of the utterance.
                      </li>
                    </ul>
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-row dense>
              <v-col cols="2">
                Rephrasing Quality
              </v-col>
              <v-col>
                <v-slider
                  v-model="RephrasingQuality"
                  min="0"
                  max="4"
                  step="1"
                  dense
                  persistent-hint
                />
              </v-col>
              <v-col cols="1">
                <v-tooltip
                  open-delay="200"
                  left
                  max-width="300"
                >
                  <template #activator="{ on }">
                    <v-icon
                      v-on="on"
                    >
                      mdi-help
                    </v-icon>
                  </template>
                  <p style="font-size:1.4em">
                    Evaluation the Rephrasing Quality
                    <ul>
                      <li>
                        0= Rephrasing has a significant negative impact to the dialog, resulting in little improvement in the
                        cultural appropriateness of the utterance, introduces new or additional norm violations, or distorts the
                        intended message unacceptably.
                      </li>
                      <li>
                        1= Rephrasing has a slightly negative impact.
                      </li>
                      <li>
                        2= Rephrasing is benign / basically has no impact.
                      </li>
                      <li>
                        3= Rephrasing helps slightly
                      </li>
                      <li>
                        4= Rephrasing has a significant positive impact on the dialog by making the utterance culturally
                        appropriate, while staying loyal to the original meaning.
                      </li>
                    </ul>
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        <v-row>
          <v-switch
            v-model="DelayedRemediation"
            label="Delayed Remediation"
          />
        </v-row>
      </v-card>
    </template>
  </v-stepper>
</template>

<style scoped lang="scss">

</style>
