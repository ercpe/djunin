$(document).ready(function () {
	$('.djunin-graph').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			$.get(url, function(graph_data){
				$.plot($(elem), graph_data['datarows'], graph_data['options']);
			});
		}
	});
});