<script>
import { mapActions, mapGetters, mapState } from 'vuex';
import NavigationTitle from 'dive-common/components/NavigationTitle.vue';


export default {
  name: 'annotatorHome',
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
  <div>
    <v-app-bar app>
      <NavigationTitle :name="brandData.name" />
      <v-divider
        vertical
        width="20"
        color="white"
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
        <v-card-title style="font-size:1.75em">
          Welcome to the UMD Annotator Home Page
        </v-card-title>
        <v-card-text style="font-size:1.5em">
          Some generic instructions for the annotator to perform actions.
        </v-card-text>
      </v-card>
    </v-container>
</div>
</template>
