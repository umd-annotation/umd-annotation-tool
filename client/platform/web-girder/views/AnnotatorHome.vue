<script>
import { mapActions, mapGetters, mapState } from 'vuex';
import NavigationTitle from 'dive-common/components/NavigationTitle.vue';
import BrandIcon from 'dive-common/components/BrandIcon.vue';
import TerpsicoreImage from 'dive-common/assets/TerpsichoreImage.jpg';

export default {
  name: 'annotatorHome',
  components: {
    NavigationTitle,
    BrandIcon,
  },
  props: {
  },
  inject: ['girderRest'],
  data: () => ({
    runningJobIds: [],
    TerpsicoreImage,
  }),
  computed: {
    ...mapGetters('Location', ['locationRoute']),
    ...mapState('Brand', ['brandData']),
    isAdmin() {
      if (this.girderRest) {
        return this.girderRest?.user?.admin || false;
      }
      return false;
    },
    username() {
      if (this.girderRest) {
        return this.girderRest?.user?.login;
      }
      return '';
    },
  },
  async created() {
    this.girderRest.$on('logout', this.onLogout);
  },
  beforeDestroy() {
    this.girderRest.$off('logout', this.onLogout);
  },
  methods: {
    ...mapActions('Location', ['setRouteFromLocation']),
    onLogout() {
      this.$router.push({ name: 'login' });
    },
    logout() {
      this.girderRest.logout();
    },
    goTo(link) {
      window.open(link, '_blank');
    },
  },
};
</script>

<template>
  <div>
  <div>
    <v-app-bar app>
      <NavigationTitle :name="brandData.name" />
      <BrandIcon />
      <v-divider
        vertical
        width="20"
        color="white"
        style="margin-left:20px"
      />
      <h2 class="pl-5">
        Annotator Home
      </h2>
      <v-spacer />
      <div>
        <h3 style="width:100%; text-align:center">
          {{ username }}
        </h3>
        <v-btn
          text
          style="width:100%; text-align:center"
          @click="logout"
        >
          Logout
        </v-btn>
      </div>
    </v-app-bar>
    <v-banner
      v-if="brandData.alertMessage"
      color="warning"
      app
    >
      <v-icon
        class="pr-2"
        large
      >
        mdi-alert-circle
      </v-icon>
      {{ brandData.alertMessage }}
    </v-banner>
  </div>
  <v-container style="margin-top:64px">
      <v-card class="mt-5">
        <v-spacer />
        <v-card-title >
          <div style="width:100%; font-size:1.75em;" class="text-center">
            Welcome to the UMD Terpsichore Annotator Home Page
          </div>
        </v-card-title>
        <v-card-text style="font-size:1.5em; text-align: center;">
          <div class="brandImage">
            <v-row>
              <img style="margin:auto" width="200" :src="TerpsicoreImage" />
            </v-row>
            <v-tooltip
              open-delay="200"
              close-delay="1500"
              bottom
              max-width="200"
            >
              <template #activator="{ on, attrs }">
                <v-icon
                    v-on="on"
                    v-bind="attrs"
                    class="icon"
                    x-small
                >
                    mdi-information
            </v-icon>
              </template>
              <span>The Muse Terpsichore by
                <a href="#" @click="goTo('https://www.flickr.com/photos/45238035@N02/5065121595')">
                  Becante
                </a>
                is licensed under
                <a href="#" @click="goTo('https://creativecommons.org/licenses/by-sa/4.0/deed.en')">
                    Creative Commons Attribution 2.0 Generic
                </a>
            </span>
            </v-tooltip>
        </div>
          <p>
            Please contact the project coordinator for information about project assignments.
          </p>
          <p>
            For questions, comments, and troubleshooting, contact terpsi_support@umd.edu
          </p>
        </v-card-text>
      </v-card>
    </v-container>
</div>
</template>

<style lang="scss" scoped>
.brandImage {
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
