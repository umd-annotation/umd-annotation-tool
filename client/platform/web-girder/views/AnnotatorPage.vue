<script>
import { mapActions, mapGetters, mapState } from 'vuex';
import NavigationTitle from 'dive-common/components/NavigationTitle.vue';


export default {
  name: 'AnnotatorPage',
  components: {
    NavigationTitle,
  },
  props: {
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
      <NavigationTitle :name="brandData.name" />
      <v-divider
        vertical
        width="20"
        color="white"
      />
      <h2 class="pl-5">
        Annotator Landing Page
      </h2>
      <v-spacer />
      <v-btn
        text
        @click="logout"
      >
        Logout
      </v-btn>
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
