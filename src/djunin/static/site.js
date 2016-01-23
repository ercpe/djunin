$(document).ready(function () {
	$.get($('.node-graphs').data('graph-spec'), function(response) {
		for (var graph_name in response) {
			var options = response[graph_name];
			$.get(options['data_url'], function(graph_data){
				var graph_name = graph_data['graph_name']
				$.plot($('#graph-' + graph_name + '-daily'), graph_data['datarows'], options);
			});
		}
	});
});