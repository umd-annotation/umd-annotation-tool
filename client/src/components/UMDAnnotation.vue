<script lang="ts">
import {
  computed, defineComponent, ref, Ref, watch, PropType, onMounted, nextTick,
} from '@vue/composition-api';

import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import { useGirderRest } from 'platform/web-girder/plugins/girder';
import {
  useCameraStore,
  useHandler,
  useSelectedTrackId,
  useTime,
} from 'vue-media-annotator/provides';
import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import { UMDAnnotationMode } from 'platform/web-girder/store/types';


type NormsObjectValues = Record<string, 'adhered' |'violated' | 'EMPTY_NA' | 'adhered_violated'>;

export default defineComponent({
  name: 'UMDAnnotation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
  },

  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String as PropType<UMDAnnotationMode>,
      default: 'review',
    },
  },

  setup(props, { emit }) {
    const selectedTrackIdRef = useSelectedTrackId();

    const { prompt } = usePrompt();
    const { frame, maxSegment } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();
    const arousal = ref(1);
    const valence = ref(1);
    const emotionsList: Ref<string[]> = ref([]);

    const emotionsForm = ref(null);
    const arousalNudged = ref(false);
    const valenceNudged = ref(false);
    const alreadyAnnotated = ref(false);
    const nudgedVAE = computed(() => arousalNudged.value && valenceNudged.value);
    const arousalAdjusted = () => {
      arousalNudged.value = true;
    };
    const valenceAdjusted = () => {
      valenceNudged.value = true;
    };

    watch(emotionsForm, () => {
      if (emotionsForm.value !== null) {
        // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
        // @ts-ignore
        (emotionsForm.value as Vue & { validate: () => boolean }).validate();
      }
    });

    const baseEmotionsList = computed(() => {
      if (emotionsList.value.includes('No emotions')) {
        return ['No emotions'];
      }
      const root = ['Anger', 'Anticipation', 'Joy', 'Trust', 'Fear', 'Surprise', 'Sadness', 'Disgust'];
      return ['No emotions', ...root];
    });
    const multiSpeakerOptions = ref(['FALSE', 'TRUE', 'noann']);
    const multiSpeaker: Ref<'FALSE' | 'TRUE' | 'noann'> = ref('FALSE');
    const normsSelected: Ref<string[]> = ref([]);
    const baseNormsList = computed(() => {
      if (normsSelected.value.includes('None')) {
        return ['None'];
      }
      const root = [
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
      ];
      const normVariants = root
        .map((item) => [`${item} (adhered)`, `${item} (violated)`])
        .reduce((acc, x) => acc.concat(x)).sort();

      return [
        'None',
        ...normVariants,
      ];
    });
    const normsObject: Ref<NormsObjectValues> = ref({});
    const userLogin = ref('');
    const loadedAttributes = ref(false);
    let dataStore: {
      arousal?: number;
      valence?: number;
      emotionsList?: string[];
      multiSpeaker?: 'FALSE' | 'TRUE' | 'noann';
      normsSelected?: string[];
      normsObject?: NormsObjectValues;
    } = {};

    let framePlaying = -1;
    const seekBegin = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.seekToFrame(track.begin);
      }
    };
    const seekEnd = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.seekToFrame(track.end);
      }
    };
    const playSegment = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.replayFromFrame(track.begin);
        framePlaying = track.end;
      }
    };

    const checkAttributes = (trackNum: number | null, loadValues = false) => {
      // load existing attributes
      let hasAttributes = false;
      if (trackNum !== null) {
        const track = cameraStore.getAnyPossibleTrack(trackNum);
        if (track === undefined) {
          return false;
        }
        Object.keys(track.attributes).forEach((key) => {
          if (key.includes(userLogin.value)) {
            const replaced = key.replace(`${userLogin.value}_`, '');
            if (replaced === 'Valence' && props.mode === 'VAE') {
              if (loadValues) {
                valence.value = track.attributes[key] as number;
                valenceNudged.value = true;
              }
              hasAttributes = true;
            }
            if (replaced === 'Arousal' && props.mode === 'VAE') {
              if (loadValues) {
                arousal.value = track.attributes[key] as number;
                arousalNudged.value = true;
              }
              hasAttributes = true;
            }
            if (replaced === 'Emotions' && props.mode === 'VAE') {
              if (loadValues) {
                emotionsList.value = (track.attributes[key] as string).split('_');
              }
              hasAttributes = true;
            }
            if (replaced === 'MultiSpeaker' && props.mode === 'VAE') {
              if (loadValues) {
                multiSpeaker.value = (track.attributes[key] as 'TRUE' | 'FALSE' | 'noann');
              }
              hasAttributes = true;
            }
            if (replaced === 'Norms' && props.mode === 'norms') {
              if (loadValues) {
                normsObject.value = (track.attributes[key] as NormsObjectValues);
                normsSelected.value = [];
                Object.entries(normsObject.value).forEach(([normKey, val]) => {
                  const adhered = `${normKey} (adhered)`;
                  const violated = `${normKey} (violated)`;
                  if (val.includes('adhered')) {
                    normsSelected.value.push(adhered);
                  }
                  if (val.includes('violated')) {
                    normsSelected.value.push(violated);
                  }
                  if (val.includes('noann') || val.includes('EMPTY_NA')) {
                    normsSelected.value.push('None');
                  }
                });
              }
              hasAttributes = true;
            }
          }
        });
        if (loadValues) {
          emit('seek', track.begin);
        }
      }
      return hasAttributes;
    };

    const getMaxSegmentAnnotated = async () => {
      const Ids = cameraStore.camMap.value.get('singleCam')?.trackStore.annotationIds.value;
      let maxId = -1;
      if (Ids) {
        for (let i = 0; i < Ids?.length; i += 1) {
          const val = checkAttributes(i);
          if (val) {
            maxId = i;
          }
        }
      }
      const track = cameraStore.getAnyPossibleTrack(maxId + 1);
      if (track === undefined) {
        // We are at max segment
        const text = 'You have already fully annotated this video. You can choose to edit or re-do these annotations, but you should do so with caution, and generally only if you have been instructed to.';
        const res = await prompt({
          title: 'Video already annotated!',
          text,
          alert: 'warning',
          positiveButton: 'Edit anyway',
          confirm: true,
        });
        if (res) {
          handler.trackSelect(0, false);
        } else {
          alreadyAnnotated.value = true;
        }
      } else {
        handler.trackSelect(maxId + 1, false);
      }
      loadedAttributes.value = checkAttributes(maxId + 1, true);
      seekBegin();
    };
    const initialize = async () => {
      handler.setMaxSegment(0);
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        getMaxSegmentAnnotated();
      }
    };
    onMounted(() => initialize());
    loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
    watch(selectedTrackIdRef, () => {
      loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
      if (selectedTrackIdRef.value === maxSegment.value && !loadedAttributes.value) {
        // Load stored values
        if (props.mode === 'VAE') {
          if (dataStore.arousal) {
            arousal.value = dataStore.arousal;
            arousalNudged.value = true;
          }
          if (dataStore.valence) {
            valence.value = dataStore.valence;
            valenceNudged.value = true;
          }
          if (dataStore.multiSpeaker) {
            multiSpeaker.value = dataStore.multiSpeaker;
          }
          if (dataStore.emotionsList) {
            emotionsList.value = dataStore.emotionsList;
          }
        }
        if (props.mode === 'norms') {
          if (dataStore.normsSelected) {
            normsSelected.value = dataStore.normsSelected;
          }
          if (dataStore.normsObject) {
            normsObject.value = dataStore.normsObject;
          }
        }
        dataStore = {};
      }
      if (selectedTrackIdRef.value !== null) {
        handler.setMaxSegment(selectedTrackIdRef.value);
      }
    });


    const hasPrevious = computed(() => (
      selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0));

    const hasNext = computed(() => {
      if (props.mode === 'review') {
        return true;
      }
      if (selectedTrackIdRef.value !== null) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value + 1);
        if (newTrack) {
          return checkAttributes(selectedTrackIdRef.value);
        }
        return false;
      }
      return false;
    });

    const submit = async () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getPossibleTrack(selectedTrackIdRef.value);
        // Set attributes;
        if (track === undefined) {
          return;
        }
        if (props.mode === 'VAE' || props.mode === 'review') {
          track.setAttribute(`${userLogin.value}_Valence`, valence.value);
          track.setAttribute(`${userLogin.value}_Arousal`, arousal.value);
        }
        if (props.mode === 'VAE' || props.mode === 'review') {
          track.setAttribute(`${userLogin.value}_Emotions`, emotionsList.value.join('_'));
          track.setAttribute(`${userLogin.value}_MultiSpeaker`, multiSpeaker.value);
        }
        if (props.mode === 'norms' || props.mode === 'review') {
          track.setAttribute(`${userLogin.value}_Norms`, normsObject.value);
        }
        // save the file
        handler.save();
        const oldTrackNum = selectedTrackIdRef.value;
        const newTrack = cameraStore.getAnyPossibleTrack(oldTrackNum + 1);
        if (newTrack) {
          handler.trackSelectNext(1, true);
        } else {
          alreadyAnnotated.value = true;
        }
        if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value !== oldTrackNum) {
          arousal.value = 1;
          valence.value = 1;
          emotionsList.value = [];
          normsSelected.value = [];
          normsObject.value = {};
          multiSpeaker.value = 'FALSE';
          await nextTick();
          arousalNudged.value = false;
          valenceNudged.value = false;
        }
      }
    };
    const changeTrack = (direction: -1 | 1) => {
      if (selectedTrackIdRef.value === maxSegment.value) {
        if (props.mode === 'VAE') {
          dataStore.arousal = arousal.value;
          dataStore.valence = valence.value;
          dataStore.multiSpeaker = multiSpeaker.value;
          dataStore.emotionsList = emotionsList.value;
          arousalNudged.value = true;
          valenceNudged.value = true;
        }
        if (props.mode === 'norms') {
          dataStore.normsSelected = normsSelected.value;
          dataStore.normsObject = normsObject.value;
        }
      }
      arousal.value = 1;
      valence.value = 1;
      emotionsList.value = [];
      normsSelected.value = [];
      normsObject.value = {};
      arousalNudged.value = false;
      valenceNudged.value = false;
      multiSpeaker.value = 'FALSE';

      handler.trackSelectNext(direction, true);
    };

    const syncNorms = (data: string[]) => {
      const keys = Object.keys(normsObject.value);

      for (let i = 0; i < keys.length; i += 1) {
        if (!normsSelected.value.includes(keys[i])) {
          delete normsObject.value[keys[i]];
        }
      }
      if (data.includes('None')) {
        normsObject.value.None = 'EMPTY_NA';
      } else {
        for (let i = 0; i < data.length; i += 1) {
          let adhered = data[i].includes('(adhered)');
          let violated = data[i].includes('(violated)');
          const baseKey = data[i].replace('(adhered)', '').replace('(violated)', '').trim();
          if (normsObject.value[baseKey]) {
            const existing = normsObject.value[baseKey];
            if (existing === 'adhered') {
              adhered = true;
            }
            if (existing === 'violated') {
              violated = true;
            }
          }
          if (adhered && violated) {
            normsObject.value[baseKey] = 'adhered_violated';
          } else if (adhered) {
            normsObject.value[baseKey] = 'adhered';
          } else if (violated) {
            normsObject.value[baseKey] = 'violated';
          }
        }
      }
    };

    watch(() => frame.value, () => {
      if (framePlaying !== -1 && frame.value >= framePlaying) {
        handler.pausePlayback();
        framePlaying = -1;
      }
      if ((props.mode !== 'review' && !['changepoint', 'remediation'].includes(props.mode)) && frame.value > (150 + (maxSegment.value + 2) * 450)) {
        handler.pausePlayback();
        if (selectedTrackIdRef.value !== null) {
          const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
          if (track) {
            handler.seekToFrame(150 + (maxSegment.value + 2) * 450);
          }
        }
      }
    });

    const outsideSegment = computed(() => {
      if ((!['changepoint', 'remediation'].includes(props.mode) && props.mode !== 'review')
      && selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (frame.value > track.end || frame.value < track.begin) {
          return true;
        }
        return false;
      }
      return true;
    });

    const updateEmotions = (data: string[]) => {
      if (data.includes('No emotions')) {
        emotionsList.value = ['No emotions'];
      }
    };

    const normsValid = ref(false);
    const VAEValid = ref(false);

    const submitValid = computed(() => {
      if (props.mode === 'norms') {
        return normsValid.value;
      } if (props.mode === 'VAE') {
        if (nudgedVAE.value) {
          return VAEValid.value;
        }
      }
      return false;
    });

    return {
      alreadyAnnotated,
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      arousal,
      valence,
      emotionsList,
      baseEmotionsList,
      multiSpeakerOptions,
      multiSpeaker,
      baseNormsList,
      normsSelected,
      normsObject,
      frame,
      outsideSegment,
      loadedAttributes,
      normsValid,
      VAEValid,
      submitValid,
      submit,
      changeTrack,
      syncNorms,
      seekBegin,
      seekEnd,
      playSegment,
      updateEmotions,
      //refs
      arousalNudged,
      valenceNudged,
      arousalAdjusted,
      valenceAdjusted,
      emotionsForm,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <div v-if="!alreadyAnnotated">
      <v-row
        dense
        class="scroll-sticky"
      >
        <h2 class="mr-4 mt-1">
          Segment {{ selectedTrackIdRef }}
        </h2>
        <div class="ml-2 mt-2">
          <tooltip-btn
            small
            icon="mdi-skip-previous"
            tooltip-text="Seek to first frame of segment"
            @click="seekBegin"
          />
          <tooltip-btn
            small
            icon="mdi-replay"
            tooltip-text="Playback current Segment"
            @click="playSegment"
          />
          <tooltip-btn
            small
            icon="mdi-skip-next"
            tooltip-text="Seek to end of the frame"
            @click="seekEnd"
          />
        </div>
        <v-spacer />
        <v-btn
          color="primary"
          :disabled="!hasPrevious"
          class="mx-2"
          @click="changeTrack(-1)"
        >
          Prev
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!hasNext"
          class="mx-2"
          @click="changeTrack(1)"
        >
          Next
        </v-btn>
      </v-row>
      <div v-if="mode ==='VAE' || mode ==='review'">
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-row dense>
              <v-col cols="2">
                Valence
              </v-col>
              <v-col>
                <v-slider
                  v-model="valence"
                  min="1"
                  max="1000"
                  step="1"
                  dense
                  persistent-hint
                  :hint="!valenceNudged ? 'Valence must be adjusted' : ''"
                  @change="valenceAdjusted"
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
                    Move the slider to rate the level of valence displayed by the speaker in
                    the current segment (from the
                    most negative to the most positive; the middle point indicates neutral valence).
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
            <v-row dense>
              <v-col
                cols="2"
                class="d-flex justify-end"
              >
                <span class="emoji">☹️</span>
              </v-col>
              <v-col class="valencegradient" />
              <v-col cols="1">
                <span class="emoji">🙂</span>
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
                Arousal
              </v-col>
              <v-col>
                <v-slider
                  v-model="arousal"
                  min="1"
                  max="1000"
                  step="1"
                  dense
                  persistent-hint
                  :hint="!arousalNudged ? 'Arousal must be adjusted' : ''"
                  @change="arousalAdjusted"
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
                    Move the slider to rate the level of arousal displayed by the speaker in
                    the current segment (from the
                    most calm/low energy to the most excited/high energy).
                  </p>
                </v-tooltip>
              </v-col>
            </v-row>
            <v-row dense>
              <v-col
                cols="2"
                class="d-flex justify-end"
              >
                <span class="emoji">😴</span>
              </v-col>
              <v-col class="arrousalgradient" />
              <v-col cols="1">
                <span class="emoji">😳</span>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </div>
      <div v-if="mode ==='VAE' || mode === 'review'">
        <v-row dense>
          <v-col cols="11">
            <h3>
              Emotions
            </h3>
          </v-col>
          <v-col>
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
                Indicate emotion categories expressed by the speaker in the current segment.
                Select as many categories
                as applicable. Select “No emotion” if the speaker does not express
                any particular emotion.
              </p>
            </v-tooltip>
          </v-col>
        </v-row>
        <v-row
          dense
          class="bottomborder"
        >
          <v-col>
            <v-form
              ref="emotionsForm"
              v-model="VAEValid"
            >
              <v-select
                v-model="emotionsList"
                :items="baseEmotionsList"
                chips
                multiple
                outlined
                clearable
                persistent-hint
                hint="Select one or more Emotions"
                required
                :menu-props="{maxHeight: 600}"
                :rules="[v => !!v.length || 'Must select an Emotion']"
                deletable-chips
                @change="updateEmotions($event)"
              />
            </v-form>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <h4>Multispeaker</h4>
            <v-radio-group
              v-model="multiSpeaker"
              row
            >
              <v-radio
                v-for="n in multiSpeakerOptions"
                :key="n"
                :label="n"
                :value="n"
                class="mx-3"
                style="min-height:32px; max-height:32px"
              />
            </v-radio-group>
          </v-col>
        </v-row>
      </div>
      <div v-if="mode === 'norms' || mode ==='review'">
        <v-row dense>
          <v-col cols="11">
            <h3>
              Social Norms
            </h3>
          </v-col>
          <v-col>
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
                Select all observable social norm categories employed by the speaker in the current
                segment. For each social norm identified,
                indicate whether it is adhered to or violated by the speaker. Select “None” to
                indicate that no observable social norms are present in the segment.
                Click “Submit” when done.
              </p>
            </v-tooltip>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-form v-model="normsValid">
              <v-select
                v-model="normsSelected"
                :items="baseNormsList"
                chips
                multiple
                solo
                outlined
                clearable
                persistent-hint
                hint="Select one or more Norms"
                deletable-chips
                :menu-props="{maxHeight: 600}"
                required
                :rules="[v => !!v.length || 'Must select a Norm']"
                @change="syncNorms($event)"
              />
            </v-form>
          </v-col>
        </v-row>
      </div>
      <v-row>
        <v-col>
          <v-btn
            :color="loadedAttributes ? 'warning' : 'success'"
            :disabled="outsideSegment || !submitValid"
            @click="submit"
          >
            {{ loadedAttributes ? 'Update' : 'Submit' }}
          </v-btn>
        </v-col>
      </v-row>
      <v-row>
        <v-alert
          v-if="(outsideSegment && mode && !['changepoint', 'remediation'].includes(mode))"
          outlined
          dense
          type="warning"
          class="mx-3"
        >
          Outside Current segment.  Return to the segment to submit or update.
          <v-btn
            color="primary"
            @click="seekBegin()"
          >
            Return to Segment
          </v-btn>
        </v-alert>
      </v-row>
    </div>
    <div v-else>
      <h3> Video Completed</h3>
    </div>
  </v-container>
</template>

<style scoped lang="scss">
.scroll-sticky {
  z-index: 99;
  position: -webkit-sticky; /* Safari */
  position: sticky;
  top: 0px;
  background-color: rgb(30, 30, 30);
}
.valencegradient {
  background: rgb(255,255,255);
  background: radial-gradient(circle, rgba(166, 166, 166, 1) 0%, rgba(0,0,0,1) 100%);
  clip-path: polygon(0 0, 0 100%, 50% 50%, 100% 100%, 100% 0, 50% 50%);

}
.arrousalgradient{
  background: rgb(255,255,255);
  background: linear-gradient(90deg, rgb(166, 166, 166) 0%, rgba(0,0,0,1) 100%);
  clip-path: polygon(100% 0, 0 50%, 100% 100%);
}
.maincontainer {
  font-size: 1.2em !important;
}
.emoji {
  font-size: 1.75em;
  font-family: 'Noto Color Emoji';

}
.bottomborder{
  border-bottom: 3px solid gray;
}
.v-sheet.v-list {
  background-color: rgb(76, 76, 76);
  font-weight: bolder;
}
</style>
