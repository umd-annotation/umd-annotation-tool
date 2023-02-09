<script>
import { mapActions, mapGetters, mapState } from 'vuex';

import { GirderSearch } from '@girder/components/src';
import NavigationTitle from 'dive-common/components/NavigationTitle.vue';
import UserGuideButton from 'dive-common/components/UserGuideButton.vue';
import BrandIcon from 'dive-common/components/BrandIcon.vue';
import JobsTab from './JobsTab.vue';

export default {
  name: 'GenericNavigationBar',
  components: {
    NavigationTitle,
    UserGuideButton,
    JobsTab,
    GirderSearch,
    BrandIcon,
  },
  inject: ['girderRest'],
  data: () => ({
    runningJobIds: [],
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
  },
};
</script>

<template>
  <div>
    <v-app-bar app>
      <BrandIcon />
      <NavigationTitle :name="brandData.name" />
      <v-tabs
        icons-and-text
        color="accent"
        class="mx-2"
      >
        <v-tab
          exact
          :to="locationRoute"
        >
          Data
          <v-icon>mdi-database</v-icon>
        </v-tab>
        <JobsTab />
        <v-tab
          :to="`/annotatorHome`"
        >
          Annotator Home <v-icon>mdi-home</v-icon>
        </v-tab>
        <v-tab
          v-if="isAdmin"
          :to="`/admin`"
        >
          Admin <v-icon>mdi-badge-account</v-icon>
        </v-tab>
      </v-tabs>
      <v-spacer />
      <GirderSearch
        :search-types="['user', 'folder']"
        placeholder="search"
        hide-options-menu
        hide-search-icon
        class="mx-2 grow"
        @select="setRouteFromLocation"
      />
      <user-guide-button v-if="false" />
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
</template>

<style lang="scss">
.rotate {
  animation: rotation 1.5s infinite linear;
}

@keyframes rotation {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(359deg);
  }
}
</style>
