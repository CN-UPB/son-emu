/*
 * App routing rules.
*/
angular.module('app')
  .config(function($stateProvider, $urlRouterProvider) {
  // For any unmatched url, redirect to root state
  $urlRouterProvider.otherwise("/home");
  
  // Now set up the states
  $stateProvider
    .state('home', {
      url: "/home",
      templateUrl: "app/scripts/components/home/home.tpl.html",
      controller: 'HomeCtrl'
    })

    .state('stacks', {
      url: "/datacenters/{datacenterId}/{port}",
      templateUrl: "app/scripts/components/stacks/stack.tpl.html",
      controller: 'StacksCtrl'
    });
});