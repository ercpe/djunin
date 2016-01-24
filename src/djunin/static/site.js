$(document).ready(function () {
	$('.djunin-graph').each(function(i, elem) {
		$.get($(elem).data('url'), function(graph_data){
			$.plot($(elem), graph_data['datarows'], graph_data['options']);
		})
	});
});