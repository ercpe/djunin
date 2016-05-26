
function Datarows(datarows, values) {

	this.all = function() {
		var all = {};
		$.each(Object.keys(datarows), function(idx, name) {
			var datarow = {
				name: name,
				values: $.map(values, function(row) {
					return {
						date: new Date(row[0]),
						value: row[1][name],
						y: row[1][name], // required for stacking
					}
				}),
				draw: datarows[name].draw,
				color: datarows[name].color,
				label: datarows[name].label,
				sameas: datarows[name].sameas,
				value_min: datarows[name].value_min,
				value_max: datarows[name].value_max,
				value_current: datarows[name].value_current
			};
			all[name] = datarow;
		});
		return all;
	}();

	this.isStacked = function(draw) {
		return draw == 'AREASTACK' || draw == 'STACK';
	}

	this.stacked_datarow_names = function() {
		var all = this.all;
		var f = this.isStacked;
		return $.grep(Object.keys(all), function(name) {
			return f(all[name].draw)
		});
	};

	this.unstacked_datarow_names = function() {
		var all = this.all;
		var f = this.isStacked;
		return $.grep(Object.keys(all), function(name) { return f(all[name].draw) }, true);
	};

	this.get_many = function(names) {
		var a = [];
		for (var i=0; i < names.length; i++) {
			a.push(this.all[names[i]]);
		}
		return a;
	}

	this.stacked = this.get_many(this.stacked_datarow_names());
	this.unstacked = this.get_many(this.unstacked_datarow_names());

	// move AREA datarows from unstacked to stacked if there it at least one stacked on
	if (this.stacked.length) {
		// if there is at lease on stackable datarow, move all AREA datarow from unstacked to stacked
		var a = this;
		var del_names = [];
		$.each(this.unstacked, function(idx, datarow) {
			if (datarow.draw == 'AREA') {
				a.stacked.push(datarow);
				del_names.push(datarow.name);
			}
		});
		$.each(del_names, function(idx, s) {
			a.unstacked.splice(s, 1);
		});
	}

	this.dates = $.map(values, function(d) { return d.date; });
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

	this.datarows = null;
	this.values = null;
	this.yaxis = null;

	this.debug_mode = false;

	this.debug = function(s) {
		if (this.debug_mode) console.log(s);
	}

	//if (this.debug_mode && this.scope != 'day') return;

	// time scale over the whole width of our area
	this.xScale = d3.time.scale().range([0, this.width]);

	this.xAxisNumTicks = {
		'day': this.numXAxisTicks,
		'week': 7,
		'month': this.numXAxisTicks,
		'year': 12,
	}

	this.xAxisTickFormats = {
		'day': d3.time.format("%H:%M"),
		'week': d3.time.format("%d"),
		'month': d3.time.format("Week %U"),
		'year': d3.time.format("%b"),
	}

	// x axis definition
	this.xAxis = d3.svg.axis()
					.scale(this.xScale)
					.orient("bottom")
					.innerTickSize(-this.height)
					.outerTickSize(0) // remove tick marker at min/max
					.ticks(this.xAxisNumTicks[this.graph_scope])
					.tickFormat(this.xAxisTickFormats[this.graph_scope]);

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
			dataType: 'json',
		}).done(function(response) {
			// bail out if response contains no data
			if (!response.values.length) {
				this.container.parent().append($('<div class="alert alert-info">This graph has no data</div>'));
				$('.djunin-graph', this.container.parent()).remove();
				$('.djunin-graph-legend', this.container.parent()).remove();
				return;
			}

			this.prepare_data(response);
			this.render_graph();
		}).fail(function(response) {
			this.container.parent().append($('<div class="alert alert-danger">There was an error fetching the data for this graph</div>'));
			$('.djunin-graph', this.container.parent()).remove();
			$('.djunin-graph-legend', this.container.parent()).remove();
			return;
		});
	}

	this.render_graph = function() {
		// set up the color domain based on the datarow names
		this.color = d3.scale.category20().domain(Object.keys(this.datarows.all));

		// setup the x axis of the graph
		this.xScale.domain(d3.extent(this.datarows.dates));

		// add the x axis to the graph object
		this.svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + this.height + ")")
		  	.call(this.xAxis);

		// setup y scale of the graph
		this.debug_mode && this.debug("Graph min: " + this.y_min() + ", max: " + this.y_max());
		this.yScale.domain([this.y_min(), this.y_max()]).nice(this.numYAxisTicks);
		var graph_yaxis = this.svg
								.append("g")
								.attr("class", "y axis")
								.call(this.yAxis);

		// add the y axis label if available
		if (this.yaxis.label) {
			graph_yaxis.append("text")
				.attr("transform", "rotate(-90)")
				.attr("y", 0 - this.margin.left)
				.attr("x",0 - (this.height / 2))
				.attr("dy", "1em")
				.style("text-anchor", "middle")
				.text(this.yaxis.label);
		}

		// insert legend now to avoid to many jumps during page load
		this.makeLegend();

		// add datarows to the svg
		var graph = this;
		c = function(aa) {
			return graph.getColor(aa);
		}

		$.each([this.stack(this.datarows.stacked), this.datarows.unstacked], function(idx, data) {
			graph.svg.selectAll(".datarow-" + idx)
				.data(data)
				.enter()
					.append("g")
					.attr("class", "datarow-" + idx)
					.append("path")
					.each(function(d) {
						if (d.draw == 'AREA' || d.draw == 'AREASTACK' || d.draw == 'STACK') {
							d3.select(this)
								.attr("class", "area")
								.attr("d", function(d) { return graph.area(d.values); })
								.style("fill", c)
								.style("opacity", '0.7');
						} else {
							d3.select(this)
								.attr("class", "line " + d.draw.toLowerCase())
								.attr('data-datarow', d.name)
								.attr("d", function(d) { return graph.line(d.values); })
								.style("stroke", c)
						}
					});
		});

		// append zero line
		this.svg
				.append("g")
					.attr("class", "x axis zero")
					.attr("transform", "translate(0," + this.yScale(0) + ")")
					.call(this.xAxis.tickFormat("").tickSize(0));
	}

	this.prepare_data = function(response) {
		// create Date objects from timestamps
		$.each(response.values, function(idx, elem) {
			elem.date = new Date(elem[0]);
		});

		this.yaxis = response.yaxis;

		this.datarows = new Datarows(response.datarows, response.values);
	}

	// helper function to get the color for a datarows. This is either the value from the datarow config
	// or the value from the color() definition
	this.getColor = function(d) {
		return d.color || this.color(this.datarows.all[d.name || d].sameas || d.name)
	}

	this.y_min = function() {
		return typeof this.yaxis.graph_min == "undefined" ?
						this.yaxis.value_min :
						this.yaxis.graph_min;
	}

	this.y_max = function() {
		return this.yaxis.graph_max && this.yaxis.value_max ?
				Math.max(this.yaxis.graph_max, this.yaxis.value_max) :
				(this.yaxis.graph_max || this.yaxis.value_max);

	}

	this.makeLegend = function() {
		// insert makeshift legend
		var legend_container = $(this.container_id + "-legend");
		var legend = $('<table class="table table-condensed legend">')
		legend.append($('<tr><th colspan="2"></th><th>Min</th><th>Max</th><th>Current</th></tr>'));

		var graph = this;

		$.each(Object.keys(this.datarows.all), function(idx, datarow_name) {
			var datarow = graph.datarows.all[datarow_name];
			if (datarow.sameas) return;

			var label = datarow.label || datarow.name;
			var tr = $('<tr></tr>')
						.attr('data-datarow', datarow.name)
						.append($('<td></td>').append($('<span class="color" style="background-color: ' +  graph.getColor(datarow) + '"></span>')))
						.append($('<td class="small"></td>')
									.text(label)
									.attr('title', datarow.info || label)
						)
						.append($('<td class="small"></td>').text(datarow.value_min ? graph.legendFormat(datarow.value_min) : '-'))
						.append($('<td class="small"></td>').text(datarow.value_max ? graph.legendFormat(datarow.value_max) : '-'))
						.append($('<td class="small"></td>').text(datarow.value_current ? graph.legendFormat(datarow.value_current) : '-'));
			tr.hover(function() {
				var name = $(this).data('datarow');
				$('svg path[data-datarow=' + name + ']', graph.container).addClass('highlighted');
				var other = graph.datarows.all[name].sameas;
				if (other) {
					var output = $.grep(Object.keys(graph.datarows), function(dr_name, idx) {
						return graph.datarows.all[dr_name].sameas == name;
					});
					if (output.length) $('svg path[data-datarow=' + other + ']', graph.container).addClass('highlighted');
				}
			}, function() {
				$('svg path', graph.container).removeClass('highlighted');
			});
			legend.append(tr);
		});

		$(legend_container).append(legend);
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