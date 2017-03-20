/*
 * Stacks Controller.
*/
angular.module('app').controller('StacksCtrl', function StacksController($scope, $stateParams, $http) {
  $scope.activeItemIndex = 0;

  $scope.datacenter = $stateParams.datacenterId;
  $scope.port = $stateParams.port;

	$scope.getStackNameFromIndex = function(index){
		if($scope.servers !== undefined)
			return $scope.servers[index].name;
	};

	$scope.setActiveStack = function(index) {
		$scope.activeItemIndex = index;

		$scope.memoryUsageOptions = {legend: { display: true, position: "bottom", animation: false }};
		$scope.memoryUsageData = [];
		$scope.memoryUsageLabels = ["Used", "Free"];		
		
  	$scope.cpuUsageLabels = []; 
  	$scope.cpuUsageData = [];
  	$scope.cpuUsageSeries = ['Usage']; 
  	$scope.cpuUsageOptions = {
  		animation: false
  	};
	};

	$scope.getListOfServers = function() {
		$http.get('http://0.0.0.0:' + $scope.port + '/v2.1/' + $scope.datacenter + '/servers').then(function(response) {
			$scope.servers = response.data.servers;

			$scope.setActiveStack($scope.activeItemIndex);

			$scope.getDataFromServer();
			setInterval(function(){ $scope.getDataFromServer(); }, 5000);
	 	});
	};

	$scope.getListOfServers();


	$scope.getDataFromServer = function() {
		$http.get('http://localhost:3000/v1/monitor/' + $scope.getStackNameFromIndex($scope.activeItemIndex)).then(function(response) {
	 		$scope.emuData = response.data;
	 	
	 		if($scope.cpuUsageLabels.length > 5) {
				$scope.cpuUsageLabels.shift();
				$scope.cpuUsageData.shift();
			}

			var currentDate = new Date();
			var timeToShow = (currentDate.getHours() < 10 ? '0':'') + currentDate.getHours() + ":" + (currentDate.getMinutes() < 10 ? '0':'') + currentDate.getMinutes() + ":" + (currentDate.getSeconds() < 10 ? '0':'') + currentDate.getSeconds();
			
			$scope.cpuUsageLabels.push(timeToShow);
		  $scope.cpuUsageData.push($scope.emuData['CPU_%']);	

		  $scope.memoryUsageData = [$scope.emuData.MEM_used * 500, ($scope.emuData.MEM_limit - $scope.emuData.MEM_used)];
	  });	
	};
});