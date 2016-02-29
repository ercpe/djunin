(function ($) {
	function init(plot) {
		plot.hooks.drawOverlay.push(function (plot, ctx) {
			var yaxis = plot.getYAxes()[0];
			var legend = $('.djunin-graph-legend', plot.getPlaceholder().parent());

			var data = plot.getData();
			for (var i = 0; i < data.length; i++) {
				var row = $('.label_' + data[i].internal_name).parents('tr');

				$('.datarow-min', row).text(yaxis.tickFormatter(data[i].min_value, yaxis));
				$('.datarow-max', row).text(yaxis.tickFormatter(data[i].max_value, yaxis));
			}
		})
	}

	$.plot.plugins.push({
		init: init,
		options: {},
		name: "djunin",
		version: "0.1"
	});
})(jQuery);