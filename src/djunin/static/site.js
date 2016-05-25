function render_graphs(container_id, url) {
//	var container = $('#' + container_id)
//	var graph_scope = container.data('graph-scope');
//
//	var debug = false;
//
//	//if (debug && graph_scope != "day") return;
//
//	var numXAxisTicks = 5;
//	var numYAxisTicks = 5;

//	function xTicks(axis) {
//		var format = "";
//
//		var numTicks = numXAxisTicks;
//
//		switch (graph_scope) {
//			case "day":
//				format = d3.time.format("%H:%M");
//				break;
//			case "week":
//				format = d3.time.format("%d");
//				numTicks = 7;
//				break;
//			case "month":
//				format = d3.time.format("Week %U");
//				break;
//			case "year":
//				format = d3.time.format("%b");
//				numTicks = 12;
//				break;
//		}
//		axis.ticks(numTicks).tickFormat(format);
//		return axis;
//	}

//	var margin = {top: 20, right: 0, bottom: 30, left: 50},
//    	width = container.width() - margin.left - margin.right,
//    	height = container.height() - margin.top - margin.bottom;

//	var color = d3.scale.category20();

//	var xScale = d3.time.scale().range([0, width]);
//	var xAxis = d3.svg.axis().scale(xScale)
//					.orient("bottom")
//					.innerTickSize(-height)
//					.outerTickSize(0) // remove tick marker at min/max
//					;
//	xAxis = xTicks(xAxis);

//	var yScale = d3.scale.linear().range([height, 0]);
//	var yAxisTickFormat = d3.format("s");
//	var yAxis = d3.svg.axis().scale(yScale)
//					.orient("left")
//					.innerTickSize(-width)
//					.outerTickSize(0)  // remove tick marker at min/max
//					.ticks(numYAxisTicks).tickFormat(yAxisTickFormat);
//
//	var line = d3.svg.line().interpolate("basis")
//		.defined(function(d) { return d.value != null; }) // makes null values a gap
//		.x(function(d) { return xScale(d.date); })
//		.y(function(d) { return yScale(d.value); });

//	var area = d3.svg.area()
//		.defined(function(d) { return d.value != null; }) // makes null values a gap
//		.x(function(d) {
//			//debug && console.log("X: " + xScale(d.date));
//			return xScale(d.date); })
//		.y0(function(d) {
//			//debug && console.log(d.name + ": y0: " + d.y0)
//			return yScale(d.y0 || 0)
//		})
//		.y1(function(d) {
//			//debug && console.log(d.name + ": y1: " + (d.y0 + d.value) + " (value: " + d.value + ") - fixed: " + ((d.y0 || 0) + d.value) + " -> " + yScale((d.y0 || 0) + d.value));
//			return yScale((d.y0 || 0) + d.value);
//		});

//	var legendFormat = d3.format('.2s')

//	var stack = d3.layout.stack().values(function(d) { return d.values; });

//	var svg = d3.select('#' + container_id).append("svg")
//			.attr("width", width + margin.left + margin.right)
//			.attr("height", height + margin.top + margin.bottom)
//		.append("g")
//			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	$.get(url, function(response) {

//		if (!response.values.length) {
//			$(container).parent().append($('<div class="alert alert-info">This graph has no data</div>'));
//			$('.djunin-graph', $(container).parent()).remove();
//			$('.djunin-graph-legend', $(container).parent()).remove();
//
//			return;
//		}

		// translate into domain objects
		$.each(response.values, function(idx, elem) {
			elem.date = new Date(elem[0]);
		});

		function getColor(d) {
			return d.color || color(response.datarows[d.name].sameas || d.name)
		}

		// build a color map for our datarows
		color.domain(Object.keys(response.datarows));

		var unstacked_datarows = [];
		var stacked_datarows = [];

		$.each(Object.keys(response.datarows), function(idx, name) {
			var o = {
				name: name,
				values: $.map(response.values, function(row) {
					return {
						date: new Date(row[0]),
						value: row[1][name],
						y: row[1][name], // required for stacking
					}
				}),
				draw: response.datarows[name].draw,
				color: response.datarows[name].color,
			};

			if (o.draw == "AREASTACK" || o.draw == "STACK") {
				stacked_datarows.push(o);
			} else {
				unstacked_datarows.push(o);
			}
		});

		if (stacked_datarows.length) {
			// if there is at lease on stackable datarow, move all AREA datarow from
			// unstacked to stacked
			unstacked_datarows = $.grep(unstacked_datarows, function(dr, idx) {
				var keep = dr.draw != 'AREA';

				if (!keep) {
					stacked_datarows.push(dr);
				}

				return keep;
			});
		}


		if (debug) {
			console.log("unstacked:");
			console.log(unstacked_datarows);
			console.log("stacked:");
			console.log(stacked_datarows);
			console.log("Min: Graph: " + response.yaxis.graph_min + ", Value: " + response.yaxis.value_min);
			console.log("Max: Graph: " + response.yaxis.graph_max + ", Value: " + response.yaxis.value_max);
		}

		y_min = typeof response.yaxis.graph_min == "undefined" ? response.yaxis.value_min : response.yaxis.graph_min;
		y_max = response.yaxis.graph_max && response.yaxis.value_max ?
				Math.max(response.yaxis.graph_max, response.yaxis.value_max) :
				(response.yaxis.graph_max || response.yaxis.value_max);
		if (y_min == 0 && y_max == 0) y_max = 1;
		if (y_min == y_max) y_min = 0;
		debug && console.log("min: " + y_min + ", max: " + y_max);
		yScale.domain([y_min, y_max]).nice(numYAxisTicks);

		// set the domain for the x axis to the dates
		xScale.domain(d3.extent(response.values, function(d) { return d.date; }));

		// add the x axis to the graph object
		svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
		  	.call(xAxis);

		// add the y axis to the graph
		var graph_yaxis = svg.append("g").attr("class", "y axis").call(yAxis);

		// add the y axis label if available
		if (response.yaxis.label) {
			graph_yaxis.append("text")
				.attr("transform", "rotate(-90)")
				.attr("y", 0 - margin.left)
				.attr("x",0 - (height / 2))
				.attr("dy", "1em")
				.style("text-anchor", "middle")
				.text(response.yaxis.label);
		}

		// manipulate the datarows in the graph
		$.each([stack(stacked_datarows), unstacked_datarows], function(idx, data) {
			svg.selectAll(".datarow-" + idx)
				.data(data)
				.enter()
					.append("g")
					.attr("class", "datarow-" + idx)
					.append("path")
					.each(function(d) {
						if (d.draw == 'AREA' || d.draw == 'AREASTACK' || d.draw == 'STACK') {
							d3.select(this)
								.attr("class", "area")
								.attr("d", function(d) { return area(d.values); })
								.style("fill", getColor)
								.style("opacity", '0.7');
						} else {
							d3.select(this)
								.attr("class", "line")
								.attr('data-datarow', d.name)
								.attr("d", function(d) { return line(d.values); })
								.style("stroke", getColor)
						}
					});
		});

		// append zero line
		svg.append("g").attr("class", "x axis zero").attr("transform", "translate(0," + yScale(0) + ")").call(xAxis.tickFormat("").tickSize(0));

		// insert makeshift legend
		var legend_container = $('#' + $(container).attr('id') + "-legend");
		var legend = $('<table class="table table-condensed legend">')
		legend.append($('<tr><th colspan="2"></th><th>Min</th><th>Max</th><th>Current</th></tr>'));
		$.each([stacked_datarows, unstacked_datarows], function(idx, data) {
			$.each(data, function(j, dr) {
				var config = response.datarows[dr.name];
				if (config.sameas) return;

				var label = config.label || dr.name;
				var tr = $('<tr></tr>')
							.attr('data-datarow', dr.name)
							.append($('<td></td>').append($('<span class="color" style="background-color: ' +  getColor(dr) + '"></span>')))
							.append($('<td class="small"></td>')
										.text(label)
										.attr('title', config.info || label)
							)
							.append($('<td class="small"></td>').text(config.value_min ? legendFormat(config.value_min) : '-'))
							.append($('<td class="small"></td>').text(config.value_max ? legendFormat(config.value_max) : '-'))
							.append($('<td class="small"></td>').text(config.value_current ? legendFormat(config.value_current) : '-'));
				tr.hover(function() {
					var name = $(this).data('datarow');
					$('svg path[data-datarow=' + name + ']', $(container)).addClass('highlighted');
					var other = response.datarows[name].sameas;
					if (!other) {
						var output = $.grep(Object.keys(response.datarows), function(dr_name, idx) { return response.datarows[dr_name].sameas == name; });
						if (output.length) $('svg path[data-datarow=' + other + ']', $(container)).addClass('highlighted');
					}
				}, function() {
					$('svg path', $(container)).removeClass('highlighted');
				});
				legend.append(tr);
			});
		});
		$(legend_container).append(legend);
	});
}

function DjuninGraph(container_id, url) {
	this.container_id = container_id;
	this.container = $(container_id);
	this.url = url;
	this.scope = this.container.data('graph-scope');

	this.margin = {top: 20, right: 0, bottom: 30, left: 50};
	this.width = this.container.width() - this.margin.left - this.margin.right;
    this.height = this.container.height() - this.margin.top - this.margin.bottom;

	this.numXAxisTicks = 5;
	this.numYAxisTicks = 5;

	this.debug_mode = true;

	this.debug = function(s) {
		if (this.debug_mode) console.log(s);
	}

	this.color = d3.scale.category20();

	// time scale over the whole width of our area
	this.xScale = d3.time.scale().range([0, this.width]);

	// x axis definition
	this.xAxis = d3.svg.axis().scale(this.xScale).orient("bottom").innerTickSize(-this.height)
					.outerTickSize(0); // remove tick marker at min/max

	function xTicks(axis) {
		var format = "";
		var numTicks = this.numXAxisTicks;

		switch (this.graph_scope) {
			case "day":
				format = d3.time.format("%H:%M");
				break;
			case "week":
				format = d3.time.format("%d");
				numTicks = 7;
				break;
			case "month":
				format = d3.time.format("Week %U");
				break;
			case "year":
				format = d3.time.format("%b");
				numTicks = 12;
				break;
		}
		axis.ticks(numTicks).tickFormat(format);
		return axis;
	}
	this.xAxis = xTicks(this.xAxis); // fixme

	// linear scale over the complete height
	this.yScale = d3.scale.linear().range([this.height, 0]);

	// SI unit format for y axis. TODO: Is this always good?
	this.yAxisTickFormat = d3.format("s");

	// y axis definition
	this.yAxis = d3.svg.axis().scale(this.yScale)
					.orient("left")
					.innerTickSize(-this.width)
					.outerTickSize(0)  // remove tick marker at min/max
					.ticks(this.numYAxisTicks).tickFormat(this.yAxisTickFormat);

	// definition for every line in our graphs
	this.line = d3.svg.line().interpolate("basis")
		.defined(function(d) { return d.value != null; }) // makes null values a gap
		.x(function(d) { return this.xScale(d.date); }) // convert all values for x and y in our data to a px value in our svg
		.y(function(d) { return this.yScale(d.value); });

	// definition for areas in our graphs
	this.area = d3.svg.area()
		.defined(function(d) { return d.value != null; }) // makes null values a gap
		.x(function(d) {
			//debug && console.log("X: " + xScale(d.date));
			return this.xScale(d.date);
		})
		.y0(function(d) {
			//debug && console.log(d.name + ": y0: " + d.y0)
			return this.yScale(d.y0 || 0)
		})
		.y1(function(d) {
			//debug && console.log(d.name + ": y1: " + (d.y0 + d.value) + " (value: " + d.value + ") - fixed: " + ((d.y0 || 0) + d.value) + " -> " + yScale((d.y0 || 0) + d.value));
			return this.yScale((d.y0 || 0) + d.value);
		});

	// format for items in the legend table. .2 means two decimal points
	this.legendFormat = d3.format('.2s')

	// stack layout definition
	this.stack = d3.layout.stack().values(function(d) { return d.values; });

	this.render = function() {
		this.debug("Rendering " + this.scope + " in " + this.container + " with data from " + this.url);

		// create svg object
		this.svg = d3
					.select(this.container_id)
					.append("svg")
						.attr("width", this.width + this.margin.left + this.margin.right)
						.attr("height", this.height + this.margin.top + this.margin.bottom)
					.append("g")
						.attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")"); // translate every coordinate into the inner area

		// fetch data from server
		$.ajax({
			url: this.url,
			context: this,
			complete: this.render_graph
		});
	}

	this.render_graph = function(response) {
		// bail out if response contains no data
		if (true || !response.values.length) {
			this.container.parent().append($('<div class="alert alert-info">This graph has no data</div>'));
			$('.djunin-graph', this.container.parent()).remove();
			$('.djunin-graph-legend', this.container.parent()).remove();
			return;
		}
	}
}

$(document).ready(function () {

	$('#site-search').autocomplete({
		serviceUrl: $('#site-search').data('url'),
		width: '300px',
		onSelect: function (suggestion) {
			window.location.href = suggestion.data;
			return false;
		}
	});

	$('.djunin-graph:visible').each(function(i, elem) {
		var url = $(elem).data('url');
		if (url) {
			var g = new DjuninGraph('#' + elem.id, url);
			g.render();
		}
	});
});