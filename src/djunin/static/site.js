function suffixFormatter(base, val, axis) {
	if (val == 0) return val;

	var absval = Math.abs(val);
	var units = ['k', 'M', 'G', 'T', 'P']

	for (var i=0; i < units.length; i++) {
		var x = Math.pow(base, i+1);

		if (absval < x) {
			var suffix = "";
			if (i > 0) suffix = units[i-1]

			var xcalc = val / Math.pow(base, i);
			if (val < 0) xcalc * -1;

			var decimals = axis.tickDecimals;
			if ((xcalc === Number(xcalc) && xcalc % 1 !== 0) && axis.tickDecimals == 0) {
				decimals = 1;
			}

			return xcalc.toFixed(decimals) + " " + suffix;
		}
	}
	return val;
}

function align_legend(plot, offset) {
	$.each(plot.getYAxes(), function(idx, elem) {
		if (elem.labelWidth) {
			$('.djunin-graph-legend', $(plot.getCanvas().parentElement).parent()).css('margin-left', (elem.labelWidth + 5) + 'px');
			return false;
		}
	});
}

var updateLegendTimeout = null;
var latestPosition = null;


function draw_graphs() {
	$('.djunin-graph:visible').each(function(i, elem) {
		var url = $(elem).data('url');
		if (!url) return;

		$.get(url, function(graph_data){
			var opts = graph_data['options'];
			var meta = graph_data['_meta'];
			var legend_container = $('#graph-' + graph_data['graph_name'] + "-" + meta['scope'] + "-legend");

			if (graph_data['datarows'].length == 0) {
				$(elem).html('<div class="alert alert-info">This graph has no data.</div>');
				$(elem).css('height', 'auto');
				return;
			}

			opts['legend'] = { container: legend_container }

			if (meta['autoscale'] === true) {
				var base = meta['base'] || 1000;
				opts['yaxis']['tickFormatter'] = function(val, axis) {
					return suffixFormatter(base, val, axis);
				}
			}

			opts['crosshair'] = { mode: 'x', };
			opts['grid'] = $.extend(opts['grid'], {
				hoverable: true,
				autoHighlight: false
			});

			opts['hooks'] = {
				processOffset: align_legend,
			}

			var plot = $.plot($(elem), graph_data['datarows'], opts);

			// custom stuff for our graphs
			$('table', legend_container).css('width', '100%');
			$('tr', legend_container).append('<td class="datarow-min col-md-2"></td><td class="datarow-max col-md-2"></td><td class="datarow-current col-md-2"></td>');
			$('table', legend_container).prepend('<tr><th colspan="2"></th><th>Min</th><th>Max</th><th>Current</th></tr>');
			$('.legendLabel', legend_container).addClass('col-md-6')


			function update_legend() {
				updateLegendTimeout = null;

				var pos = latestPosition;

				var axes = plot.getAxes();
				if (pos.x < axes.xaxis.min || pos.x > axes.xaxis.max ||
					pos.y < axes.yaxis.min || pos.y > axes.yaxis.max) {
					return;
				}

				var i, j, dataset = plot.getData();
				for (i = 0; i < dataset.length; ++i) {
					var series = dataset[i];

					// Find the nearest points, x-wise
					for (j = 0; j < series.data.length; ++j) {
						if (series.data[j][0] > pos.x) {
							break;
						}
					}

					// Now Interpolate
					var y,
						p1 = series.data[j - 1],
						p2 = series.data[j];

					if (p1 == null) {
						y = p2[1];
					} else if (p2 == null) {
						y = p1[1];
					} else {
						y = p1[1] + (p2[1] - p1[1]) * (pos.x - p1[0]) / (p2[0] - p1[0]);
					}

					var formatted_value = series.yaxis.tickFormatter(y, series.yaxis);
					if (formatted_value == 0) formatted_value = 0;
					$('tr:nth-child(' + (i+2) + ') > .datarow-current', legend_container).text(formatted_value);
				}
			}


			$(elem).bind("plothover",  function (event, pos, item) {
				latestPosition = pos;
				if (!updateLegendTimeout) {
					updateLegendTimeout = setTimeout(update_legend, 50);
				}
			});

		}).fail(function() {
			$(elem).html('<div class="alert alert-danger">There was a error fetching the data for this graph.</div>');
			$(elem).css('height', 'auto');
		});
	});
}

$(document).ready(function () {

	draw_graphs();

	$('#site-search').autocomplete({
		serviceUrl: $('#site-search').data('url'),
		onSelect: function (suggestion) {
			window.location.href = suggestion.data;
			return false;
		}
	});
});