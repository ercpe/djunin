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

$(document).ready(function () {
	$('.djunin-graph:visible').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			$.get(url, function(graph_data){

				if (graph_data['datarows'].length == 0) {
					$(elem).html('<div class="alert alert-info">This graph has no data.</div>');
					$(elem).css('height', 'auto');
					return;
				}

				var opts = graph_data['options'];
				var meta = graph_data['_meta'];

				opts['legend'] = {
					container: $('#graph-' + graph_data['graph_name'] + "-" + meta['scope'] + "-legend")
				}

				if (meta['autoscale'] === true) {
					var base = meta['base'] || 1000;
					opts['yaxis']['tickFormatter'] = function(val, axis) {
						return suffixFormatter(base, val, axis);
					}
				}

				opts['hooks'] = {
					processOffset: align_legend
				}

				$.plot($(elem), graph_data['datarows'], opts);
			}).fail(function() {
				$(elem).html('<div class="alert alert-danger">There was a error fetching the data for this graph :(</div>');
				$(elem).css('height', 'auto');
			});
		}
	});

	$('#site-search').autocomplete({
		serviceUrl: $('#site-search').data('url'),
		onSelect: function (suggestion) {
			window.location.href = suggestion.data;
			return false;
		}
	});
});