$(document).ready(function () {
	$.get($('.node-graphs').data('graph-spec'), function(response) {
		for (var graph_name in response) {
			var options = response[graph_name];
			$.get(options['data_url'], function(graph_data){
				var graph_name = graph_data['graph_name'];
				if (graph_name == 'memcached_code_nys_de_bytes') {
					console.log("Options:");
					console.log(options);
					console.log("Data:")
					console.log(graph_data);
					$.plot($('#graph-' + graph_name + '-daily'), graph_data['datarows'], options);
				}
			});
		}
	});
});