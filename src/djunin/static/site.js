$(document).ready(function () {
	$('.djunin-graph').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			$.get(url, function(graph_data){
				var opts = graph_data['options'];
				opts['legend'] = {
					container: $('#graph-' + graph_data['graph_name'] + "-legend")
				}
				$.plot($(elem), graph_data['datarows'], opts);
			});
		}
	});
});