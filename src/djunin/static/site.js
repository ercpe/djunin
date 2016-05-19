/*
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

			opts['legend'] = {
				container: legend_container,
				labelFormatter: function(label, series) {
					return $('<span></span>', {
						class: "label_" + series.internal_name,
						text: label,
						title: series.description || series.long_description,
					}).prop('outerHTML');
				}
			}

			if (meta['autoscale'] === true) {
				var base = meta['base'] || 1000;
				opts['yaxis']['tickFormatter'] = function(val, axis) {
					return suffixFormatter(base, val, axis);
				}
			}

			opts['crosshair'] = { mode: 'x', };
			opts['grid'] = $.extend(opts['grid'], {
				hoverable: true,
				autoHighlight: false,
				markings: [
				     { color: '#606060', lineWidth: 1, yaxis: { from: 0, to: 0 } },
				]
			});

			opts['hooks'] = {
				processOffset: align_legend,
			}

			var plot = $.plot($(elem), graph_data['datarows'], opts);

			// custom stuff for our graphs
			$('table', legend_container).css('width', '100%');
			$('tr', legend_container).append('<td class="datarow-min col-md-2"></td><td class="datarow-max col-md-2"></td><td class="datarow-current col-md-2"></td>');
			$('table', legend_container).prepend('<tr><th colspan="2"></th><th class="datarow-min">Min</th><th class="datarow-max">Max</th><th class="datarow-current">Current</th></tr>');
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

					var formatted_value = y ? series.yaxis.tickFormatter(y, series.yaxis) : null;
					if (formatted_value === 0) formatted_value = 0;
					$('tr:nth-child(' + (i+2) + ') > .datarow-current', legend_container).text(formatted_value ? formatted_value : '-');
				}
			}

			if (window.location.hash) {
				o = $(window.location.hash);
				if (o.length) $(window).scrollTop($(window.location.hash).offset().top - 70);
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
*/

function render_graphs(container_id, url) {
	var container = $('#' + container_id)

	var margin = {top: 20, right: 80, bottom: 30, left: 50},
    	width = container.width() - margin.left - margin.right,
    	height = container.height() - margin.top - margin.bottom;

	var x = d3.time.scale().range([0, width]);
	var y = d3.scale.linear().range([height, 0]);
	var color = d3.scale.category10();

	var xAxis = d3.svg.axis().scale(x).orient("bottom");
	var yAxis = d3.svg.axis().scale(y).orient("left").ticks(5).tickFormat(d3.format("s"));

	var line = d3.svg.line().interpolate("basis")
		.defined(function(d) { return d.value != null; }) // makes null values a gap
		.x(function(d) { return x(d.date); })
		.y(function(d) { return y(d.value); });

	var svg = d3.select('#' + container_id).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	$.get(url, function(response) {
		color.domain(response.datarows);

		$.each(response.values, function(idx, elem) {
			elem.date = new Date(elem[0]);
		});

		var datarows = color.domain().map(function(name) {
			return {
				name: name,
				values: $.map(response.values, function(row) {
					return {
						date: new Date(row[0]),
						value: row[1][name]
					}
				})
			};
		});

		x.domain(d3.extent(response.values, function(d) { return d.date; }));

		y_min = response.yaxis.min || 0; // d3.min(datarows, function(c) { return d3.min(c.values, function(v) { return v.value; }); });
		y_max = response.yaxis.max || d3.max(datarows, function(c) { return d3.max(c.values, function(v) { return v.value; }); });
		y.domain([y_min, y_max]);

		svg.append("g")
		  .attr("class", "x axis")
		  .attr("transform", "translate(0," + height + ")")
		  .call(xAxis);

		var graph_yaxis = svg.append("g")
		  	.attr("class", "y axis")
		  	.call(yAxis);

		if (response.yaxis.label) {
			graph_yaxis.append("text")
			  .attr("transform", "rotate(-90)")
			  .attr("y", 6)
			  .attr("dy", "-40")
			  .style("text-anchor", "end")
			  .text(response.yaxis.label);
		}

		var datarow = svg.selectAll(".datarow").data(datarows).enter().append("g").attr("class", "datarow");
		datarow.append("path")
			.attr("class", "line")
			.attr("d", function(d) { return line(d.values); })
			.style("stroke", function(d) { return color(d.name); });

//		  city.append("text")
//			  .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
//			  .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.value) + ")"; })
//			  .attr("x", 3)
//			  .attr("dy", ".35em")
//			  .text(function(d) { return d.name; });

	});
}

function draw_graphs() {
	$('.djunin-graph:visible').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			render_graphs(elem.id, url);
		}
	});
}

$(document).ready(function () {
	draw_graphs();

	$('#site-search').autocomplete({
		serviceUrl: $('#site-search').data('url'),
		width: '300px',
		onSelect: function (suggestion) {
			window.location.href = suggestion.data;
			return false;
		}
	});

});