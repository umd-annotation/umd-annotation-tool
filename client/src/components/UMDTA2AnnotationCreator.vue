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
import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import { clientSettings } from 'dive-common/store/settings';
import { cloneDeep } from 'lodash';


export default defineComponent({
  name: 'UMDTA2Annotation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
  },

  props: {
    width: {
      type: Number,
      default: 500,
    },
  },

  setup(props, { emit }) {
    const selectedTrackIdRef = useSelectedTrackId();

    const { prompt } = usePrompt();
    const { frame, maxSegment } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();

    const firstTrack = cameraStore.getAnyPossibleTrack(0);
    clientSettings.trackSettings.newTrackSettings.modeSettings.Track.interpolate = true;
    if (firstTrack) {
      handler.trackSelect(0, false);
      handler.seekToFrame(firstTrack.begin);
    }

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


    const initialize = async () => {
      handler.setMaxSegment(99999);
      const user = await restClient.fetchUser();
    };
    onMounted(() => initialize());


    const hasPrevious = computed(() => {
      if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value - 1);
        if (newTrack) {
          return newTrack.id;
        }
        return false;
      }
      return false;
    });

    const hasNext = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value + 1);
        if (newTrack) {
          return newTrack.id;
        }
        return false;
      }
      return false;
    });

    const changeTrack = (direction: -1 | 1) => {
      handler.trackSelectNext(direction, true);
    };

    watch(() => frame.value, () => {
      if (framePlaying !== -1 && frame.value >= framePlaying) {
        handler.pausePlayback();
        framePlaying = -1;
      }
      if (frame.value > (150 + (maxSegment.value + 2) * 450)) {
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
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (frame.value > track.end || frame.value < track.begin) {
          return true;
        }
        return false;
      }
      return true;
    });

    const trackFrames = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (track) {
          return { begin: track.begin, end: track.end };
        }
      }
      return null;
    });

    const reOrderTracks = () => {
      const tracks = cameraStore.sortedTracks;
      const trackCopy = cloneDeep(tracks.value);
      trackCopy.sort((a, b) => a.begin - b.begin);
      // Now we have a sorted list by the begin point instead of the trackId.
      // So we need to update the tracks so they have the proper begin/end times
      trackCopy.forEach((item, index) => {
        const getTrack = cameraStore.getTrack(index);
        console.log(`index: ${index} : id: ${getTrack.id} begin : ${getTrack.begin} end: ${getTrack.end}`);
        console.log(`item: ${item.id} begin : ${item.begin} end: ${item.end}`);
        if (getTrack) {
          const updateBeginFeature = item.getFeature(item.begin);
          if (updateBeginFeature[0]) {
            console.log('updating begin feature');
            getTrack.deleteFeature(getTrack.begin);
            getTrack.setFeature(updateBeginFeature[0]);
          }
          const updateEndFeature = item.getFeature(item.end);
          if (updateEndFeature[0]) {
            console.log('updating end feature');
            getTrack.deleteFeature(getTrack.end);
            getTrack.setFeature(updateEndFeature[0]);
          }
        }
      });
      console.log(cameraStore.sortedTracks);
      // Now tracks should be reordered with their proper numbers
    };

    const createTurn = () => {
      const trackId = handler.addFullFrameTrack('turn', 100);
      if (trackId !== null) {
        handler.trackSelect(trackId, false);
        reOrderTracks();
        handler.save();
      }
    };
    const setFrame = (pos: 'begin' | 'end') => {
      if (selectedTrackIdRef.value !== null) {
        handler.updateFullFrame(selectedTrackIdRef.value, pos);
        reOrderTracks();
        handler.trackSelect(selectedTrackIdRef.value, false);
        handler.save();
      }
    };

    return {
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      frame,
      trackFrames,
      outsideSegment,
      changeTrack,
      seekBegin,
      seekEnd,
      playSegment,
      createTurn,
      setFrame,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <div>
      <v-row
        v-if="selectedTrackIdRef !== null"
        dense
        class="scroll-sticky"
      >
        <h2 class="mr-4 mt-1">
          Turn {{ (selectedTrackIdRef || 0) + 1 }}
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
          :disabled="hasPrevious === false"
          class="mx-2"
          @click="changeTrack(-1)"
        >
          Prev
        </v-btn>
        <v-btn
          color="primary"
          :disabled="hasNext === false"
          class="mx-2"
          @click="changeTrack(1)"
        >
          Next
        </v-btn>
      </v-row>
      <v-row>
        <v-btn
          color="primary"
          class="mx-2"
          @click="createTurn()"
        >
          Create Turn
        </v-btn>
      </v-row>
      <v-row v-if="trackFrames">
        <v-col><div><span>Begin Frame:</span><span>{{ trackFrames.begin }}</span></div></v-col>
        <v-col><div><span>End Frame:</span><span>{{ trackFrames.end }}</span></div></v-col>
      </v-row>
      <v-row v-if="selectedTrackIdRef !== null">
        <v-col>
          <v-btn
            color="primary"
            class="mx-2"
            @click="setFrame('begin')"
          >
            Set Begin Frame
          </v-btn>
        </v-col>
        <v-col>
          <v-btn
            color="primary"
            class="mx-2"
            @click="setFrame('end')"
          >
            Set End Frame
          </v-btn>
        </v-col>
      </v-row>
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
