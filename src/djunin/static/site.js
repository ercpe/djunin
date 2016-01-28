$(document).ready(function () {
	$('.djunin-graph').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			$.get(url, function(graph_data){
				var opts = graph_data['options'];
				opts['legend'] = {
					container: $('#graph-' + graph_data['graph_name'] + "-legend")
				}

				var meta = graph_data['_meta'];
				if (meta['autoscale'] === true) {
					var base = meta['base'] || 1000;
					opts['yaxis']['tickFormatter'] = function suffixFormatter(val, axis) {
						if (val == 0) {
							return val;
						}

						var absval = Math.abs(val);
						var units = ['k', 'M', 'G', 'T', 'P']

						for (var i=0; i < units.length; i++) {
							var x = Math.pow(base, i+1);

							if (absval < x) {
								var suffix = "";
								if (i > 0) suffix = units[i-1]

								var xcalc = val / Math.pow(base, i)
								if (val < 0) xcalc * -1;
								return xcalc.toFixed(axis.tickDecimals) + " " + suffix;
							}
						}
						return val;
					}
				}

				$.plot($(elem), graph_data['datarows'], opts);
			});
		}
	});
});