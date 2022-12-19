<script lang="ts">
import {
  computed, defineComponent, ref, Ref, watch, PropType, onMounted,
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
      type: String as PropType<'VAE' | 'norms' | 'changepoint' | 'emotion' | 'review'>,
      default: 'review',
    },
  },

  setup(props, { emit }) {
    const selectedTrackIdRef = useSelectedTrackId();

    const { frame, maxSegment } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();
    const arousal = ref(1);
    const valence = ref(1);
    const baseEmotionsList = ['Anger', 'Anticipation', 'Joy', 'Trust', 'Fear', 'Surprise', 'Sadness', 'Disgust'];
    const multiSpeakerOptions = ref(['FALSE', 'TRUE', 'noann']);
    const multiSpeaker: Ref<'FALSE' | 'TRUE' | 'noann'> = ref('FALSE');
    const emotionsList: Ref<string[]> = ref([]);
    const baseNormsList = ['Apology', 'Criticism', 'Greeting', 'Request', 'Persuasion', 'Thanks', 'Taking Leave', 'Admiration', 'Finalizing Negotiating/Deal', 'Refusing a Request'];
    const normsSelected: Ref<string[]> = ref([]);
    const normsObject: Ref<Record<string, 'adhered' |'violate' | 'noann' | 'EMPTY_NA'>> = ref({});
    const changePointFrame = ref(-1);
    const changePointImpact = ref(1);
    const changePointComment = ref('');
    const userLogin = ref('');
    const loadedAttributes = ref(false);

    const checkAttributes = (trackNum: number | null, loadValues = false) => {
      // load existing attributes
      let hasAttributes = false;
      if (trackNum !== null) {
        const track = cameraStore.getAnyTrack(trackNum);
        Object.keys(track.attributes).forEach((key) => {
          if (key.includes(userLogin.value)) {
            hasAttributes = true;
            if (loadValues) {
              const replaced = key.replace(`${userLogin.value}_`, '');
              if (replaced === 'Valence') {
                valence.value = track.attributes[key] as number;
              }
              if (replaced === 'Arousal') {
                arousal.value = track.attributes[key] as number;
              }
              if (replaced === 'Emotions') {
                emotionsList.value = (track.attributes[key] as string).split('_');
              }
              if (replaced === 'MultiSpeaker') {
                multiSpeaker.value = (track.attributes[key] as 'TRUE' | 'FALSE' | 'noann');
              }
              if (replaced === 'Norms') {
                normsObject.value = (track.attributes[key] as Record<string, 'adhered' |'violate' | 'noann' | 'EMPTY_NA'>);
                normsSelected.value = Object.keys(normsObject.value);
              }
            }
          }
        });
        if (loadValues) {
          track.features.forEach((feature) => {
            const currentFrame = feature.frame;
            if (feature.attributes) {
              Object.keys(feature.attributes).forEach((key) => {
                if (key.includes(userLogin.value) && feature.attributes) {
                  const attribute = feature.attributes[key];
                  const replaced = key.replace(`${userLogin.value}_`, '');
                  if (replaced === 'Impact') {
                    changePointImpact.value = attribute as number;
                    changePointFrame.value = currentFrame;
                  }
                  if (replaced === 'Comment') {
                    changePointComment.value = attribute as string;
                    changePointFrame.value = currentFrame;
                  }
                }
              });
            }
          });
          if (loadValues) {
            emit('seek', track.begin);
          }
        }
      }
      return hasAttributes;
    };

    const initialize = async () => {
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        handler.trackSelectNext(1, true);
        handler.setMaxSegment(0);
        loadedAttributes.value = checkAttributes(0);
      }
    };
    onMounted(() => initialize());
    loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
    watch(selectedTrackIdRef, () => {
      loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
      if (selectedTrackIdRef.value !== null) {
        handler.setMaxSegment(selectedTrackIdRef.value);
      }
    });


    const setCheckpoint = () => {
      changePointFrame.value = frame.value;
    };

    const hasPrevious = computed(() => (
      selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0));

    const hasNext = computed(() => {
      if (props.mode === 'changepoint' || props.mode === 'review') {
        return true;
      }
      if (selectedTrackIdRef.value !== null) {
        return checkAttributes(selectedTrackIdRef.value);
      }
      return false;
    });

    const submit = async () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        // Set attributes;
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
        // set Change Point Information
        if (props.mode === 'changepoint' || props.mode === 'review') {
          if (changePointFrame.value !== -1) {
            if (track.getFeature(changePointFrame.value)[0] === null
          || !track.getFeature(changePointFrame.value)[0]?.keyframe) {
              track.toggleKeyframe(changePointFrame.value);
            }
            track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Impact`, changePointImpact.value);
            track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Comment`, changePointComment.value);
          }
        }
        // save the file
        handler.save();
        const oldTrackNum = selectedTrackIdRef.value;
        handler.trackSelectNext(1, true);
        if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value !== oldTrackNum) {
          arousal.value = 1;
          valence.value = 1;
          emotionsList.value = [];
          normsSelected.value = [];
          normsObject.value = {};
          multiSpeaker.value = 'FALSE';
          changePointFrame.value = -1;
          changePointImpact.value = 1;
          changePointComment.value = '';
        }
      }
    };
    const goToChangePoint = () => {
      //Need to set this up
      handler.seekToFrame(changePointFrame.value);
    };
    const changeTrack = (direction: -1 | 1) => {
      arousal.value = 1;
      valence.value = 1;
      emotionsList.value = [];
      normsSelected.value = [];
      normsObject.value = {};
      multiSpeaker.value = 'FALSE';
      changePointFrame.value = -1;
      changePointImpact.value = 1;
      changePointComment.value = '';

      handler.trackSelectNext(direction, true);
    };

    const updateNorm = (item: string, value: 'adhered' | 'violate' | 'noann' | 'EMPTY_NA') => {
      normsObject.value[item] = value;
    };
    const syncNorms = () => {
      const keys = Object.keys(normsObject.value);
      for (let i = 0; i < keys.length; i += 1) {
        if (!normsSelected.value.includes(keys[i])) {
          delete normsObject.value[keys[i]];
        }
      }
    };

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
    watch(() => frame.value, () => {
      if (framePlaying !== -1 && frame.value >= framePlaying) {
        handler.pausePlayback();
        framePlaying = -1;
      }
      if ((props.mode !== 'review' && props.mode !== 'changepoint') && frame.value > (150 + (maxSegment.value + 2) * 450)) {
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
      if ((props.mode !== 'changepoint' && props.mode !== 'review')
      && selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (frame.value > track.end || frame.value < track.begin) {
          return true;
        }
        return false;
      }
      return true;
    });

    return {
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
      changePointFrame,
      changePointImpact,
      changePointComment,
      outsideSegment,
      loadedAttributes,
      setCheckpoint,
      submit,
      goToChangePoint,
      changeTrack,
      updateNorm,
      syncNorms,
      seekBegin,
      seekEnd,
      playSegment,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
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
    <p class="mt-8">
      Some instruction text to indicate to the annotator what to do.
      This could be lengthy to provide more detailed instructions or not.
    </p>
    <div v-if="mode ==='VAE' || mode ==='review'">
      <v-row dense>
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
              />
            </v-col>
            <v-col cols="1" />
          </v-row>
          <v-row dense>
            <v-col
              cols="2"
              class="d-flex justify-end"
            >
              <v-icon>mdi-emoticon-sad-outline</v-icon>
            </v-col>
            <v-col class="valencegradient" />
            <v-col cols="1">
              <v-icon>mdi-emoticon-excited-outline</v-icon>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row class="mt-4">
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
              />
            </v-col>
            <v-col cols="1" />
          </v-row>
        </v-col>
      </v-row>
    </div>
    <div v-if="mode ==='VAE' || mode === 'review'">
      <v-row>
        <v-col
          cols="3"
          class="align-self-center"
        >
          Emotions
        </v-col>
        <v-col>
          <v-select
            v-model="emotionsList"
            :items="baseEmotionsList"
            chips
            multiple
            clearable
            persistent-hint
            deletable-chips
          />
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
      <v-row>
        <v-col>
          <v-select
            v-model="normsSelected"
            :items="baseNormsList"
            chips
            label="Norms"
            multiple
            clearable
            persistent-hint
            deletable-chips
            @change="syncNorms"
          />
        </v-col>
      </v-row>
      <v-row
        v-for="item in normsSelected"
        :key="`${item}`"
      >
        <v-col>
          <h4>{{ item }}</h4>
          <v-radio-group
            v-model="normsObject[item]"
            row
          >
            <v-radio
              v-for="n in ['adhere', 'violate', 'noann', 'EMPTY_NA']"
              :key="n"
              :label="n"
              :value="n"
              class="mx-3"
              style="min-height:32px; max-height:32px"
            />
          </v-radio-group>
          <v-divider />
        </v-col>
      </v-row>
    </div>
    <div v-if="mode ==='changepoint' || mode === 'review'">
      <v-row v-if="(changePointFrame == -1)">
        <v-btn
          :disable="outsideSegment"
          @click="setCheckpoint"
        >
          Set ChangePoint {{ frame }}
        </v-btn>
      </v-row>
      <div v-if="(changePointFrame != -1)">
        <h4> Current ChangePoint : {{ changePointFrame }}</h4>
        <v-row class="mt-2 ml-2">
          <v-btn
            v-if="(frame !== changePointFrame && !disableChangePoint)"
            :disable="disableChangePoint"
            outlined
            @click="setCheckpoint"
          >
            Set Changepoint to current frame: {{ frame }}
          </v-btn>
        </v-row>
        <v-alert
          v-if="disableChangePoint"
          dense
          outlined
          type="warning"
        >
          Setting ChangePoint is disabled because the current frame {{ frame }}
          is outside of the current Segment Range
        </v-alert>
        <v-row class="mt-2 ml-2">
          <v-btn
            outlined
            @click="goToChangePoint"
          >
            Go to ChangePoint
          </v-btn>
        </v-row>
        <v-row>
          <v-col>
            <v-slider
              v-model="changePointImpact"
              label="Impact"
              min="1"
              max="5"
              step="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="changePointComment"
              outlined
              label="Comment"
            />
          </v-col>
        </v-row>
      </div>
    </div>

    <v-row>
      <v-col>
        <v-btn
          :color="loadedAttributes ? 'warning' : 'success'"
          :disabled="outsideSegment"
          @click="submit"
        >
          {{ loadedAttributes ? 'Update' : 'Submit' }}
        </v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-alert
        v-if="(outsideSegment && mode && mode !== 'changepoint')"
        outlined
        dense
        type="warning"
        class="mx-3"
      >
        Outside Current segment.  Return to the segment to submit or update.
      </v-alert>
    </v-row>
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
  background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(0,0,0,1) 100%);
  clip-path: polygon(0 0, 0 100%, 50% 70%, 100% 100%, 100% 0, 50% 30%);

}
.maincontainer {
  font-size: 1.2em !important;
}
</style>
