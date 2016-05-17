(function ($) {
	function init(plot) {

		plot.hooks.processDatapoints.push(function(plot, series, datapoints) {
			if (series.invert) {
				var points = datapoints.points, ps = datapoints.pointsize;
				for (var i = 0; i < points.length; i += ps) {
					points[i + 1] *= -1;
				}
			}
		});

		plot.hooks.drawOverlay.push(function (plot, ctx) {
			var yaxis = plot.getYAxes()[0];
			var legend = $('.djunin-graph-legend', plot.getPlaceholder().parent());

			var data = plot.getData();
			for (var i = 0; i < data.length; i++) {
				var row = $('.label_' + data[i].internal_name, legend).parents('tr');

				var min_value = data[i].min_value ? yaxis.tickFormatter(data[i].min_value, yaxis) : '-';
				var max_value = data[i].max_value ? yaxis.tickFormatter(data[i].max_value, yaxis) : '-';
				$('.datarow-min', row).text(min_value);
				$('.datarow-max', row).text(max_value);
			}
		});
	}

	$.plot.plugins.push({
		init: init,
		options: {},
		name: "djunin",
		version: "0.1"
	});
})(jQuery);