import {
  reactive, Ref, toRefs,
} from '@vue/composition-api';
import { throttle } from 'lodash';

// https://en.wikipedia.org/wiki/Flick_(time)
export const Flick = 705_600_000;

/**
 * Avoid floating point errors for common flick rates
 */
export const NTSCFlickrates: Record<string, number> = {
  '24000/1001': 29429400,
  '30000/1001': 23543520,
  '60000/1001': 11771760,
  '120000/1001': 5885880,
};

export interface Time {
  frame: Readonly<Ref<number>>;
  flick: Readonly<Ref<number>>;
  frameRate: Readonly<Ref<number>>;
  originalFps: Readonly<Ref<number | null>>;
  maxSegment: Readonly<Ref<number>>;
  maxFrame: Readonly<Ref<number>>;
}

export type SetTimeFunc = (
  { frame, flick }: { frame: number; flick: number }
) => void;

/**
 * The Time Observer is used when some privileged section
 * of the app should be allowed to set time, but the rest
 * of the general app should only read time.
 */
export default function useTimeObserver() {
  const data = reactive({
    frame: 0,
    flick: 0,
    frameRate: NaN,
    originalFps: null as number | null,
    maxFrame: 0,
    maxSegment: -1,
  });

  function initialize({ frameRate, originalFps }: {
    frameRate: number; originalFps: number | null;
  }) {
    if (typeof frameRate !== 'number') {
      throw new Error(`frameRate=${frameRate} is not a number`);
    }
    data.frameRate = frameRate;
    data.originalFps = originalFps;
  }

  const updateTime: SetTimeFunc = throttle(({
    frame, flick, maxFrame, maxSegment,
  }:
    { frame: number; flick: number; maxFrame?: number; maxSegment?: number }) => {
    data.frame = frame;
    data.flick = flick;
    if (maxFrame !== undefined) {
      data.maxFrame = Math.max(maxFrame, data.maxFrame);
    }
    if (maxSegment !== undefined) {
      data.maxSegment = Math.max(data.maxSegment, maxSegment);
    }
  });

  const setMaxSegment = (segment: number) => {
    data.maxSegment = Math.max(data.maxSegment, segment);
  };

  const time: Time = toRefs(data);

  return {
    initialize,
    updateTime,
    setMaxSegment,
    time,
  };
}
