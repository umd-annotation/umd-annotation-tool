<script lang="ts">
// eslint-disable-next-line @typescript-eslint/ban-ts-ignore
// @ts-ignore
import miniLogo from 'dive-common/assets/miniLogo.svg';
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  setup() {
    const goTo = (link: string) => {
      window.open(link, '_blank');
    };
    return {
      miniLogo,
      goTo,
    };
  },
});
</script>

<template>
  <div class="brandLogo">
    <img
      :src="miniLogo"
      width="25"
      height="25"
    >
    <v-tooltip
      open-delay="200"
      close-delay="1500"
      bottom
      max-width="200"
    >
      <template #activator="{ on, attrs }">
        <v-icon
          v-bind="attrs"
          class="icon"
          x-small
          v-on="on"
        >
          mdi-information
        </v-icon>
      </template>
      <span>Terpsichore symbol by
        <a
          href="#"
          @click="goTo('https://commons.wikimedia.org/wiki/User:Kwamikagami')"
        >
          Kwamikagami
        </a>
        is licensed under
        <a
          href="#"
          @click="goTo('https://creativecommons.org/licenses/by-sa/4.0/deed.en')"
        >
          Creative Commons Attribution-Share Alike 4.0 International
        </a>
      </span>
    </v-tooltip>
  </div>
</template>

<style lang="scss" scoped>
.brandLogo {
  position: relative;
}
.icon {
  position: absolute;
  right: 0px;
  bottom: 0px;
  &:hover {
    cursor: pointer;
  }
}
.v-tooltip__content {
  pointer-events: initial;
}

</style>
