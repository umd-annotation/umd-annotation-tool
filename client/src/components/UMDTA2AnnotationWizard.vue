<script lang="ts">
import {
  defineComponent, PropType, ref, Ref, watch,
} from '@vue/composition-api';
import { useSelectedTrackId } from 'vue-media-annotator/provides';

export type NormsList =
  | 'Admiration'
  | 'Apology'
  | 'Criticism'
  | 'Finalizing Negotiating/Deal'
  | 'Greeting'
  | 'Persuasion'
  | 'Refusing a Request'
  | 'Request'
  | 'Taking Leave'
  | 'Thanks';

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

  components: {},

  props: {
    annotations: {
      type: Object as PropType<TA2Annotation>,
      required: true,
    },
    outsideSegment: {
      type: Boolean,
      required: true,
    },
  },

  setup(props, { emit }) {
    const annotationState: Ref<'ASRMTQuality' | 'Norms' | 'AlertRephrasing'> = ref('ASRMTQuality');
    const selectedTrackIdRef = useSelectedTrackId();

    const steps = ref([
      'ASR/Translation Quality',
      'Norm Adherence/Violation',
      'Remediation Qaulity',
    ]);
    const stepper = ref(1);
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
    watch(() => props.annotations, () => {
      stepper.value = 1;
      ASRQuality.value = props.annotations.ASRQuality || 0;
      MTQuality.value = props.annotations.MTQuality || 0;
      AlertsQuality.value = props.annotations.AlertsQuality || 0;
      DelayedRemediation.value = props.annotations.DelayedRemediation || false;
      Norms.value = props.annotations.Norms || {};
      selectedNorms.value = Object.keys(Norms.value) as NormsList[];
    });
    watch(selectedNorms, () => {
      const addNorms: Partial<Record<NormsList, TA2NormStatus>> = {};
      selectedNorms.value.forEach((norm) => {
        if (!addNorms[norm]) {
          addNorms[norm] = {
            status: (props.annotations.Norms && props.annotations.Norms[norm].status) || 'adhered',
            remediation: (props.annotations.Norms && props.annotations.Norms[norm].remediation) || 0,
          };
        }
      });
      Norms.value = addNorms;
    });
    const advanceStep = (currentStep: 'ASRMTQuality' | 'Norms' | 'AlertRephrasing') => {
      const annotationUpdate: TA2Annotation = { };
      if (currentStep === 'ASRMTQuality') {
        annotationUpdate.ASRQuality = ASRQuality.value;
        annotationUpdate.MTQuality = MTQuality.value;
      } else if (currentStep === 'Norms') {
        annotationUpdate.Norms = Norms.value as Record<NormsList, TA2NormStatus>;
      } else if (currentStep === 'AlertRephrasing') {
        annotationUpdate.AlertsQuality = AlertsQuality.value;
        annotationUpdate.DelayedRemediation = DelayedRemediation.value;
        annotationUpdate.RephrasingQuality = RephrasingQuality.value;
      }
      emit('save', annotationUpdate);
      if (currentStep !== 'AlertRephrasing') {
        stepper.value += 1;
      } else {
        emit('next-turn');
      }
    };

    const updateNorm = (norm: NormsList, field: 'status' | 'remediation', value: 'adhered' | 'violated' | number) => {
      if (field === 'status') {
        if (Norms.value && Norms.value[norm] !== undefined) {
          (Norms.value[norm] as TA2NormStatus).status = value as 'adhered' | 'violated';
        }
      }
      if (field === 'remediation') {
        if (Norms.value[norm]) {
          (Norms.value[norm] as TA2NormStatus).remediation = value as number;
        }
      }
    };
    return {
      annotationState,
      steps,
      stepper,
      ASRQuality,
      MTQuality,
      Norms,
      baseNorms,
      selectedNorms,
      AlertsQuality,
      RephrasingQuality,
      DelayedRemediation,
      selectedTrackIdRef,
      advanceStep,
      updateNorm,
    };
  },
});
</script>


<template>
  <v-stepper
    v-model="stepper"
    style="width:100%"
    non-linear
  >
    <v-stepper-header>
      <v-stepper-step
        :complete="stepper > 1"
        step="1"
        editable
      >
        ASR/MT
      </v-stepper-step>

      <v-divider />

      <v-stepper-step
        :complete="stepper > 2"
        step="2"
        editable
      >
        Norms
      </v-stepper-step>

      <v-divider />

      <v-stepper-step
        step="3"
        editable
      >
        Remediation
      </v-stepper-step>
    </v-stepper-header>

    <v-stepper-items>
      <v-stepper-content step="1">
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
                    min="0"
                    max="3"
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
                          0: Very low quality, inadequate; overall gist of message and details may be very difficult to
                          comprehend without relying on contextual clues.
                        </li>
                        <li>
                          1: Tending toward low quality, but minimally adequate; overall gist of message and most
                          details is comprehensible with some difficulty
                        </li>
                        <li>
                          2: Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing
                          (interpretation) elements but mainly comprehensible
                        </li>
                        <li>
                          3: Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and
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
                    min="0"
                    max="3"
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
                          0: Very low quality, inadequate; overall gist of message and details may be very difficult to
                          comprehend without relying on contextual clues.
                        </li>
                        <li>
                          1: Tending toward low quality, but minimally adequate; overall gist of message and most
                          details is comprehensible with some difficulty
                        </li>
                        <li>
                          2: Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing
                          (interpretation) elements but mainly comprehensible
                        </li>
                        <li>
                          3: Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and
                          ceiling condition interpretation).
                        </li>
                      </ul>
                    </p>
                  </v-tooltip>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
          <v-row class="mx-2">
            <v-spacer />
            <v-btn
              color="primary"
              class="mb-2"
              @click="advanceStep('ASRMTQuality')"
            >
              Next Step
            </v-btn>
          </v-row>
        </v-card>
      </v-stepper-content>

      <v-stepper-content step="2">
        <v-card
          title="Norm Adherence/Violation"
          flat
        >
          <v-row>
            <v-select
              v-model="selectedNorms"
              label="Norms"
              multiple
              :items="baseNorms"
              chips
              clearable
              deletable-chips
              class="mx-5"
            />
          </v-row>
          <v-list v-if="Norms">
            <v-list-item
              v-for="(item,key) in Norms"
              :key="`${key}_track_${selectedTrackIdRef}_${item.status}`"
            >
              <v-row dense>
                <v-col>
                  <h5 class="mr-2">
                    {{ key }}:
                  </h5>
                </v-col>
                <v-col>
                  <v-select
                    v-if="item && item.status"
                    label="status"
                    :items="['adhered', 'violated']"
                    :value="item.status"
                    @change="updateNorm(key, 'status', $event)"
                  />
                </v-col>
                <v-col>
                  <v-select
                    v-if="item && item.remediation !== undefined"
                    :disabled="item && item.status === 'adhered'"
                    label="status"
                    item-text="title"
                    item-value="value"
                    :items="[
                      { title: 'Unnecessary', value: 0 },
                      { title: 'Recommended', value: 1 },
                      { title: 'Necessary', value: 2 },
                    ]"
                    :value="item.remediation"
                    @change="updateNorm(key, 'remediation', $event)"
                  />
                </v-col>
              </v-row>
            </v-list-item>
          </v-list>
          <v-row class="mx-2">
            <v-spacer />
            <v-btn
              color="primary"
              class="mb-2"
              @click="advanceStep('Norms')"
            >
              Next Step
            </v-btn>
          </v-row>
        </v-card>
      </v-stepper-content>

      <v-stepper-content step="3">
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
                <v-col cols="4">
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
                          0: Alerts have a siginficant negative impact to the dialog by distracting the speaker or are categorically inaccurate
                        </li>
                        <li>
                          1: Alerts have a slight negative impact by distracting the speaker or are slightly inaccurate.
                        </li>
                        <li>
                          2: Alerts are benign/basically have no impact
                        </li><li>
                          3: Alerts help slightly, lead to a slightly more culturally appropriate utterance.
                        </li>
                        <li>
                          4: Alerts have a significant positive impact on the dialog by generating accruate alerts that lead to significantly improved cultural appropriatenesss of the utterance.
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
                <v-col cols="4">
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
                          0: Rephrasing has a significant negative impact to the dialog, resulting in little improvement in the
                          cultural appropriateness of the utterance, introduces new or additional norm violations, or distorts the
                          intended message unacceptably.
                        </li>
                        <li>
                          1: Rephrasing has a slightly negative impact.
                        </li>
                        <li>
                          2: Rephrasing is benign / basically has no impact.
                        </li>
                        <li>
                          3: Rephrasing helps slightly
                        </li>
                        <li>
                          4: Rephrasing has a significant positive impact on the dialog by making the utterance culturally
                          appropriate, while staying loyal to the original meaning.
                        </li>
                      </ul>
                    </p>
                  </v-tooltip>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
          <v-row class="mx-3">
            <v-col>
              <v-switch
                v-model="DelayedRemediation"
                label="Delayed Remediation"
              />
            </v-col>
          </v-row>
          <v-row class="mx-2">
            <v-spacer />
            <v-btn
              color="primary"
              class="mb-2"
              @click="advanceStep('AlertRephrasing')"
            >
              Next Turn
            </v-btn>
          </v-row>
        </v-card>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</template>

<style scoped lang="scss">
</style>
