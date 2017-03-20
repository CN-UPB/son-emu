/*
 * Home Controller.
*/
angular.module('app').controller('HomeCtrl', function HomeController($scope, $http) {
  $scope.title = 'List of DataCenters';

  $scope.selected = { node: null };

  $http.get('http://0.0.0.0:4000/v1/topo').then(function(response) {
		$scope.nodes = response.data.nodes;
 	});
});