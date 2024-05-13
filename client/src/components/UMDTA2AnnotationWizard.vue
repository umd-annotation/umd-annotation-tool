<script lang="ts">
import {
  defineComponent,
  onMounted,
  PropType,
  ref,
  Ref,
  watch,
} from '@vue/composition-api';
import { UMDAnnotationMode } from 'platform/web-girder/store/types';
import { useSelectedTrackId } from 'vue-media-annotator/provides';

export type NormsList =
  | 'Apology'
  | 'Criticism'
  | 'Greeting'
  | 'Request'
  | 'Persuasion'
  | 'Thanks'
  | 'Taking Leave'
  | 'Admiration'
  | 'Finalizing Negotiation/Deal'
  | 'Refusing a Request'
  | 'Requesting Information'
  | 'Granting a Request'
  | 'Disagreement'
  | 'Respond to Request for Information'
  | 'Acknowledging Thanks'
  | 'Interrupting'
  | 'No Norm';

export const NormListMapping = [
  { named: 'No Norm', id: 100, groups: ['LC1', 'LC2', 'LC3'] },
  { named: 'Apology', id: 101, groups: ['LC1', 'LC2', 'LC3'] },
  { named: 'Criticism', id: 102, groups: ['LC1', 'LC2'] },
  { named: 'Greeting', id: 103, groups: ['LC1', 'LC2', 'LC3'] },
  { named: 'Request', id: 104, groups: ['LC1'] },
  { named: 'Persuasion', id: 105, groups: ['LC1'] },
  { named: 'Thanks', id: 106, groups: ['LC1', 'LC2', 'LC3'] },
  { named: 'Taking Leave', id: 107, groups: ['LC1'] },
  { named: 'Admiration', id: 108, groups: ['LC1', 'LC2', 'LC3'] },
  { named: 'Finalizing Negotiation/Deal', id: 109, groups: ['LC1', 'LC2'] },
  { named: 'Refusing a Request', id: 110, groups: ['LC1', 'LC2'] },
  { named: 'Requesting Information', id: 111, groups: ['LC2', 'LC3'] },
  { named: 'Granting a Request', id: 112, groups: ['LC2', 'LC3'] },
  { named: 'Disagreement', id: 113, groups: ['LC2', 'LC3'] },
  { named: 'Respond to Request for Information', id: 114, groups: ['LC3'] },
  { named: 'Acknowledging Thanks', id: 115, groups: ['LC3'] },
  { named: 'Interrupting', id: 116, groups: ['LC3'] },
];

export interface TA2NormStatus {
  status: 'adhered' | 'violated';
  remediation: number; //0 -unecessary, 1 recommended, 2 necessary
}

export interface TA2Annotation {
  ASRQuality?: number; //Quality number from 0-3
  MTQuality?: number; // Quality number from 0-3
  AlertsQuality?: number | null; // Quality number from 0-4
  RephrasingQuality?: number | null; // Quality number from 0-4
  DelayedRemediation?: boolean;
  Norms?: Record<NormsList, TA2NormStatus>;
}

const helpDialogTextBase = {
  ASRQuality: {
    title: 'Evaluating the ASR Quality',
    start: 0,
    list: [
      'Very low quality, inadequate; overall gist of message and details may be very difficult to comprehend without relying on contextual clues or impossible to comprehend',
      'Tending toward low quality, but minimally adequate; overall gist of message and most details is comprehensible with some difficulty',
      'Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing (interpretation) elements but mainly comprehensible',
      'Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and ceiling condition interpretation).',
    ],
  },
  MTQuality: {
    title: 'Evaluating the Translation Quality',
    start: 0,
    list: [
      'Very low quality, inadequate; overall gist of message and details may be very difficult to comprehend without relying on contextual clues.',
      'Tending toward low quality, but minimally adequate; overall gist of message and most details is comprehensible with some difficulty',
      'Tending toward high quality, adequate; some inaccurate (ASR)/non-native (MT)/missing (interpretation) elements but mainly comprehensible',
      'Very high quality; equivalent to professional transcription (ASR)/ interpretation (MT and ceiling condition interpretation).',
    ],
  },
  AlertsQuality: {
    title: 'Evaluating the Alerts Quality',
    start: -1,
    list: [
      'Alert is inaccurate and/or vague.',
      'Alert is partially inaccurate and/or somewhat vague.',
      'Alert is accurate and specific.',
    ],
  },
  RephrashingQuality: {
    title: 'Evaluating the Rephrasing Quality',
    start: -1,
    list: [
      'Rephrasing introduces additional norm violations, and/or distorts the intended message unacceptably.',
      'Rephrasing does not make utterance more appropriate culturally or distorts the intended message slightly.',
      'Rephrasing is loyal to the original meaning and results in a significantly more culturally appropriate utterance.',
    ],
  },
};

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
    mode: {
      type: String as PropType<UMDAnnotationMode>,
      default: 'review',
    },
    LC: {
      type: String as PropType<'LC1' | 'LC2' | 'LC3' | 'LC4' | 'LC5' | 'LC6'>,
      default: 'LC1',
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
    const baseNorms = ref([
      'No Norm',
      'Apology',
      'Criticism',
      'Greeting',
      'Request',
      'Persuasion',
      'Thanks',
      'Taking Leave',
      'Admiration',
      'Finalizing Negotiation/Deal',
      'Refusing a Request',
      'Requesting Information',
      'Granting a Request',
      'Disagreement',
      'Respond to Request for Information',
      'Acknowledging Thanks',
      'Interrupting',
    ]);
    const calculateBaseNorms = () => {
      const filtered = NormListMapping.filter((item) => (item.groups.includes(props.LC || 'LC1')));
      baseNorms.value = filtered.map((item) => item.named);
    };

    onMounted(() => {
      if (props.mode === 'TA2Annotation_Norms') {
        stepper.value = 2;
      }
      if (props.mode === 'TA2Annotation_Remediation') {
        stepper.value = 3;
      }
      calculateBaseNorms();
    });
    const ASRQuality = ref(props.annotations.ASRQuality === undefined ? 0 : props.annotations.ASRQuality);
    const MTQuality = ref(props.annotations.MTQuality === undefined ? 0 : props.annotations.MTQuality);
    const AlertsQuality = ref(props.annotations.AlertsQuality === undefined ? 0 : props.annotations.AlertsQuality);
    const RephrasingQuality = ref(props.annotations.RephrasingQuality === undefined ? 0 : props.annotations.RephrasingQuality);
    const noAlerts = ref(props.annotations.AlertsQuality === null);
    const noRemediation = ref(props.annotations.RephrasingQuality === null);
    const DelayedRemediation = ref(
      props.annotations.DelayedRemediation || false,
    );
    const Norms: Ref<Partial<Record<NormsList, TA2NormStatus>>> = ref(
      props.annotations.Norms || {},
    );
    const selectedNorms: Ref<NormsList[]> = ref(
      (Object.keys(Norms.value) as NormsList[]) || [],
    );
    const helpDialog = ref(false);
    const helpDialogText: Ref<{ title: string; list: string[]; start: number }> = ref(
      helpDialogTextBase.ASRQuality,
    );

    const disableNext = ref(false);
    const disableReason = ref('');
    watch(
      () => props.annotations,
      () => {
        stepper.value = 1;
        if (props.mode === 'TA2Annotation_Norms') {
          stepper.value = 2;
        }
        if (props.mode === 'TA2Annotation_Remediation') {
          stepper.value = 3;
        }
        ASRQuality.value = props.annotations.ASRQuality || 0;
        MTQuality.value = props.annotations.MTQuality || 0;
        AlertsQuality.value = props.annotations.AlertsQuality === undefined ? 0 : props.annotations.AlertsQuality;
        noAlerts.value = props.annotations.AlertsQuality === null;
        noRemediation.value = props.annotations.RephrasingQuality === null;
        RephrasingQuality.value = props.annotations.RephrasingQuality === undefined ? 0 : props.annotations.RephrasingQuality;

        DelayedRemediation.value = props.annotations.DelayedRemediation || false;
        Norms.value = props.annotations.Norms || {};
        selectedNorms.value = Object.keys(Norms.value) as NormsList[];
      },
    );
    watch(selectedNorms, () => {
      const addNorms: Partial<Record<NormsList, TA2NormStatus>> = Norms.value;
      disableNext.value = false;
      disableReason.value = '';
      if (selectedNorms.value.includes('No Norm')) {
        Norms.value = { 'No Norm': { status: 'violated', remediation: 0 } };
        if (selectedNorms.value.length > 1) {
          disableNext.value = true;
          disableReason.value = "You have selected 'No Norms' and other values, please either select 'No Norms' only or remove it from the list";
        }
        return;
      }
      selectedNorms.value.forEach((norm) => {
        if (!addNorms[norm]) {
          addNorms[norm] = {
            status:
              (props?.annotations.Norms
                && props?.annotations.Norms[norm]?.status)
              || 'adhered',
            remediation:
              (props?.annotations.Norms
                && props?.annotations.Norms[norm]?.remediation)
              || 0,
          };
        }
      });
      Object.keys(addNorms).forEach((key) => {
        const norm = key as NormsList;
        if (!selectedNorms.value.includes(norm) && addNorms[norm]) {
          delete addNorms[norm];
        }
      });
      Norms.value = addNorms;
    });
    const advanceStep = (
      currentStep: 'ASRMTQuality' | 'Norms' | 'AlertRephrasing',
    ) => {
      const annotationUpdate: TA2Annotation = {};
      if (currentStep === 'ASRMTQuality') {
        annotationUpdate.ASRQuality = ASRQuality.value;
        annotationUpdate.MTQuality = MTQuality.value;
      } else if (currentStep === 'Norms') {
        annotationUpdate.Norms = Norms.value as Record<
          NormsList,
          TA2NormStatus
        >;
      } else if (currentStep === 'AlertRephrasing') {
        annotationUpdate.AlertsQuality = noAlerts.value ? null : AlertsQuality.value;
        annotationUpdate.DelayedRemediation = noRemediation.value ? false : DelayedRemediation.value;
        annotationUpdate.RephrasingQuality = noRemediation.value ? null : RephrasingQuality.value;
      }
      emit('save', annotationUpdate);
      if (
        currentStep !== 'AlertRephrasing'
        && props.mode === 'TA2Annotation_All'
      ) {
        stepper.value += 1;
      } else {
        emit('next-turn');
      }
    };

    const updateNorm = (
      norm: NormsList,
      field: 'status' | 'remediation',
      value: 'adhered' | 'violated' | number,
    ) => {
      if (field === 'status') {
        if (Norms.value && Norms.value[norm] !== undefined) {
          (Norms.value[norm] as TA2NormStatus).status = value as
            | 'adhered'
            | 'violated';
        }
      }
      if (field === 'remediation') {
        if (Norms.value[norm]) {
          (Norms.value[norm] as TA2NormStatus).remediation = value as number;
        }
      }
    };
    const openHelpDialog = (
      key: 'ASRQuality' | 'MTQuality' | 'AlertsQuality' | 'RephrashingQuality',
    ) => {
      helpDialogText.value = helpDialogTextBase[key];
      helpDialog.value = true;
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
      noAlerts,
      noRemediation,
      DelayedRemediation,
      selectedTrackIdRef,
      advanceStep,
      updateNorm,
      openHelpDialog,
      helpDialog,
      helpDialogText,
      disableNext,
      disableReason,
    };
  },
});
</script>


<template>
  <v-stepper
    v-model="stepper"
    style="width: 100%"
    non-linear
  >
    <v-stepper-header v-if="mode === 'TA2Annotation_All'">
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
          :title="
            mode === 'TA2Annotation_ASRMTQuality'
              ? 'ASR/Translation Quality'
              : 'TranslationQuality'
          "
          flat
        >
          <v-row
            v-if="mode === 'TA2Annotation_ASRMTQuality'"
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
                    :tick-labels="['0', '1', '2', '3']"
                    dense
                    persistent-hint
                  />
                </v-col>
                <v-col cols="1">
                  <v-icon @click="openHelpDialog('ASRQuality')">
                    mdi-help
                  </v-icon>
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
                  Translation Quality
                </v-col>
                <v-col>
                  <v-slider
                    v-model="MTQuality"
                    min="0"
                    max="3"
                    step="1"
                    :tick-labels="['0', '1', '2', '3']"
                    dense
                    persistent-hint
                  />
                </v-col>
                <v-col cols="1">
                  <v-icon @click="openHelpDialog('MTQuality')">
                    mdi-help
                  </v-icon>
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
              {{
                mode === "TA2Annotation_All" ? "Next Step" : "Save + Next Turn"
              }}
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
          <v-list v-if="Norms && Object.keys(Norms).filter((item) => item !== 'No Norm').length > 0">
            <v-list-item
              v-for="(item, key) in Norms"
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
          <v-row
            v-if="disableNext"
            class="mx-2"
          >
            <v-alert type="error">
              {{ disableReason }}
            </v-alert>
          </v-row>
          <v-row class="mx-2">
            <v-spacer />
            <v-btn
              color="primary"
              :disabled="disableNext"
              class="mb-2"
              @click="advanceStep('Norms')"
            >
              {{
                mode === "TA2Annotation_All" ? "Next Step" : "Save + Next Turn"
              }}
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
                    :disabled="noAlerts"
                    min="-1"
                    max="1"
                    step="1"
                    :tick-labels="['-1', '0', '1']"
                    dense
                    persistent-hint
                  />
                </v-col>
                <v-col cols="1">
                  <v-icon @click="openHelpDialog('AlertsQuality')">
                    mdi-help
                  </v-icon>
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
                    :disabled="noRemediation"
                    min="-1"
                    max="1"
                    step="1"
                    :tick-labels="['-1', '0', '1']"
                    dense
                    persistent-hint
                  />
                </v-col>
                <v-col cols="1">
                  <v-icon @click="openHelpDialog('RephrashingQuality')">
                    mdi-help
                  </v-icon>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
          <v-row class="mx-3">
            <v-col>
              <v-switch
                v-model="DelayedRemediation"
                :disabled="noRemediation"
                label="Delayed Remediation"
              />
            </v-col>
            <v-col>
              <v-switch
                v-model="noAlerts"
                label="No Alerts"
              />
            </v-col>
            <v-col>
              <v-switch
                v-model="noRemediation"
                label="No Remediation"
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
              Save + Next Turn
            </v-btn>
          </v-row>
        </v-card>
      </v-stepper-content>
    </v-stepper-items>
    <v-dialog
      v-model="helpDialog"
      width="500"
    >
      <v-card>
        <v-card-title>{{ helpDialogText.title }} </v-card-title>
        <v-card-text class="help-text">
          <ol :start="helpDialogText.start">
            <li
              v-for="(item, index) in helpDialogText.list"
              :key="`helpitem_${index}`"
              class="my-2"
            >
              {{ item }}
            </li>
          </ol>
        </v-card-text>
        <v-card-actions>
          <v-row>
            <v-spacer />
            <v-btn @click="helpDialog = false">
              Dismiss
            </v-btn>
            <v-spacer />
          </v-row>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-stepper>
</template>

<style scoped lang="scss">
.help-text {
  font-size: 20px !important;
}
</style>
