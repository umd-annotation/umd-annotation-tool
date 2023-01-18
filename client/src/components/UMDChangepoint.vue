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
  name: 'UMDChangepoint',

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

  setup() {
    const selectedTrackIdRef = useSelectedTrackId();

    const { frame } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();
    const changePointFrame = ref(-1);
    const changePointImpact = ref(1);
    const changePointComment = ref('');
    const userLogin = ref('');
    const loadedAttributes = ref(false);
    const changePoints: Ref<{frame: number; comment: string; impact: number}[]> = ref([]);
    const selectedChangePoint: Ref<number | null> = ref(null);

    const checkAttributes = () => {
      // load existing attributes
      changePoints.value = [];
      let hasAttributes = false;
      const store = cameraStore.camMap.value.get('singleCam');
      if (store) {
        // eslint-disable-next-line no-unused-expressions
        store?.trackStore.annotationMap.forEach((track) => {
          track.features.forEach((feature) => {
            const currentFrame = feature.frame;
            if (feature.attributes) {
              let foundFeature = false;
              Object.keys(feature.attributes).forEach((key) => {
                if (key.includes(userLogin.value) && feature.attributes) {
                  hasAttributes = true;
                  const attribute = feature.attributes[key];
                  const replaced = key.replace(`${userLogin.value}_`, '');
                  if (replaced === 'Impact') {
                    changePointImpact.value = parseInt((attribute as string), 10);
                    changePointFrame.value = currentFrame;
                    foundFeature = true;
                  }
                  if (replaced === 'Comment') {
                    changePointComment.value = attribute as string;
                    changePointFrame.value = currentFrame;
                    foundFeature = true;
                  }
                }
              });
              if (foundFeature) {
                changePoints.value.push({
                  frame: changePointFrame.value,
                  impact: changePointImpact.value,
                  comment: changePointComment.value,
                });
                const segment = Math.floor((currentFrame - 150) / 450);
                handler.setMaxSegment(segment);
              }
            }
          });
        });
      }
      return hasAttributes;
    };

    const initialize = async () => {
      handler.setMaxSegment(0);
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        handler.trackSelectNext(1, true);
        loadedAttributes.value = checkAttributes();
      }
    };
    onMounted(() => initialize());

    watch(frame, () => {
      // Determine which track we are in
      if (frame.value - 150 > 0) {
        const segment = Math.floor((frame.value - 150) / 450);
        if (selectedTrackIdRef.value !== segment) {
          handler.trackSelect(segment, false);
        }
      }
    });


    const setChangepoint = () => {
      changePointFrame.value = frame.value;
    };

    const existingFrames = computed(() => changePoints.value.map((item) => item.frame));

    const deleteChangePoint = async (index: number, save = true) => {
      const changeData = changePoints.value[index];
      const segment = Math.floor((changeData.frame - 150) / 450);
      const track = cameraStore.getAnyTrack(segment);
      if (track) {
        if (track.getFeature(changeData.frame)[0]) {
          track.removeFeatureAttribute(changeData.frame, `${userLogin.value}_Impact`);
          track.removeFeatureAttribute(changeData.frame, `${userLogin.value}_Comment`);
        }
        if (selectedChangePoint.value === index) {
          selectedChangePoint.value = null;
        }
        if (save) {
          await handler.save();
          checkAttributes();
        }
      }
    };

    const addChangepoint = (internal = false) => {
      changePoints.value.push({
        frame: frame.value,
        impact: 2,
        comment: '',
      });
      if (!internal) {
        handler.pausePlayback();
      }
      changePoints.value.sort((a, b) => a.frame - b.frame);
      const foundIndex = changePoints.value.findIndex((item) => item.frame === frame.value);
      changePointFrame.value = frame.value;
      changePointImpact.value = 0;
      changePointComment.value = '';
      selectedChangePoint.value = foundIndex;
    };

    const submit = async () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null && selectedChangePoint.value !== null) {
        if (changePoints.value[selectedChangePoint.value].frame !== changePointFrame.value) {
          const impact = changePointImpact.value;
          const comment = changePointComment.value;
          deleteChangePoint(selectedChangePoint.value, false);
          addChangepoint(true);
          changePointImpact.value = impact;
          changePointComment.value = comment;
        }
        const segment = Math.floor((changePointFrame.value - 150) / 450);
        const track = cameraStore.getAnyTrack(segment);
        // Set attributes;
        // set Change Point Information
        if (changePointFrame.value !== -1) {
          if (track.getFeature(changePointFrame.value)[0] === null
          || !track.getFeature(changePointFrame.value)[0]?.keyframe) {
            track.toggleKeyframe(changePointFrame.value);
          }
          track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Impact`, changePointImpact.value);
          track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Comment`, changePointComment.value);
        }
        // save the file
        selectedChangePoint.value = null;
        handler.save();
        checkAttributes();
      }
    };


    const frameToTime = (frameNum: number) => {
      const totalSeconds = (1 / 30) * frameNum;
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = Math.floor(totalSeconds % 3600 % 60);
      if (hours > 0) {
        return `${hours}:${minutes}:${seconds}`;
      }
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    const goToChangePoint = (frameNum: number) => {
      //Need to set this up
      handler.pausePlayback();
      handler.seekToFrame(frameNum);
      selectedChangePoint.value = null;
    };
    const changeTrack = (direction: -1 | 1) => {
      changePointFrame.value = -1;
      changePointImpact.value = 1;
      changePointComment.value = '';

      handler.trackSelectNext(direction, true);
    };

    const editChangepoint = (index: number) => {
      if (selectedChangePoint.value === index) {
        selectedChangePoint.value = null;
        return;
      }

      selectedChangePoint.value = index;
      changePointFrame.value = changePoints.value[index].frame;
      changePointImpact.value = changePoints.value[index].impact;
      changePointComment.value = changePoints.value[index].comment;
    };

    const submitValid = ref(false);

    return {
      selectedTrackIdRef,
      frame,
      changePointFrame,
      changePointImpact,
      changePointComment,
      loadedAttributes,
      changePoints,
      selectedChangePoint,
      existingFrames,
      submitValid,
      setChangepoint,
      submit,
      goToChangePoint,
      changeTrack,
      editChangepoint,
      frameToTime,
      deleteChangePoint,
      addChangepoint,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <v-row dense>
      <v-col cols="11">
        <h3>
          Changepoints
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
            Identify points (timestamps) in the video where there is a change in the conversation
            that has the potential to impact the conversation outcome.
            Indicate impact level on the scale (from most negative to most positive).
            Add a comment explaining why you indicated the changepoint. Click “Save” when done.
          </p>
        </v-tooltip>
      </v-col>
    </v-row>
    <v-btn
      :disabled="existingFrames.includes(frame)"
      color="success"
      @click="addChangepoint()"
    >
      Add Changepoint at {{ frameToTime(frame) }}
    </v-btn>
    <v-card style="max-height:30vh; overflow-y:scroll">
      <v-list>
        <v-list-item
          v-for="(item, index) in changePoints"
          :key="`${index}_${item.frame}`"
          :class="{selected: selectedChangePoint === index}"
        >
          <v-row>
            <v-col cols="2">
              <v-chip
                class="px-2"
                @click="goToChangePoint(item.frame)"
              >
                {{ frameToTime(item.frame) }}
              </v-chip>
            </v-col>
            <v-col>
              <v-tooltip
                open-delay="100"
                bottom
              >
                <template #activator="{ on }">
                  <div
                    class="comment"
                    v-on="on"
                  >
                    {{ item.comment }}
                  </div>
                </template>
                <span
                  class="ma-0 pa-1"
                >
                  {{ item.comment }}
                </span>
              </v-tooltip>
            </v-col>
            <v-col cols="1">
              <v-icon @click="editChangepoint(index)">
                mdi-pencil
              </v-icon>
            </v-col>
            <v-col cols="1">
              <v-icon
                color="error"
                @click="deleteChangePoint(index)"
              >
                mdi-delete
              </v-icon>
            </v-col>
          </v-row>
        </v-list-item>
      </v-list>
    </v-card>
    <div v-if="selectedChangePoint !== null">
      <v-row v-if="(changePointFrame == -1)">
        <v-btn
          @click="setChangepoint"
        >
          Set ChangePoint {{ frame }}
        </v-btn>
      </v-row>
      <div v-if="(changePointFrame != -1)">
        <h4> Current ChangePoint Time : {{ frameToTime(changePointFrame) }}</h4>
        <v-row class="mt-2 ml-2">
          <v-btn
            v-if="(frame !== changePointFrame)"
            outlined
            :disabled="existingFrames.includes(frame)"
            @click="setChangepoint()"
          >
            Set Changepoint to current time: {{ frameToTime(frame) }}
          </v-btn>
        </v-row>
        <v-form v-model="submitValid">
          <v-row>
            <v-col>
              <v-slider
                v-model="changePointImpact"
                label="Impact"
                min="1"
                max="5"
                step="1"
                ticks="always"
                :rules="[v => v >= 0 || 'Set the Impact Value']"
                required
                :tick-size="10"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea
                v-model="changePointComment"
                outlined
                :rules="[v => v.length > 0 || 'Comment is required']"
                required
                label="Comment"
              />
            </v-col>
          </v-row>
        </v-form>
      </div>
    </div>
    <v-row>
      <v-btn
        v-if="selectedChangePoint !== null"
        color="warning"
        class="mx-2"
        :disabled="!submitValid"
        @click="submit"
      >
        Save
      </v-btn>
    </v-row>
  </v-container>
</template>

<style lang="scss">
.scroll-sticky {
  z-index: 99;
  position: -webkit-sticky; /* Safari */
  position: sticky;
  top: 0px;
  background-color: rgb(30, 30, 30);
}

.selected {
    border: 2px solid cyan;
}
.comment {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.v-slider__tick{
    background-color: rgba(190, 203, 245, 0.422);
}

.v-slider__tick--filled{
    background-color: #0277bd;
}

</style>
