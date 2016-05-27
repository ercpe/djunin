
function Datarows(datarows, graph_order, values) {

	this.all = function() {
		var l = [];
		$.each(Object.keys(datarows), function(idx, name) {
			var datarow = datarows[name];
			datarow.name = name;

			// set the draw type of the current datarow. The draw_type is a high-level description of the actual .draw
			// property (e.g. LINE1, LINE2 and LINE3) are all 'line's).
			datarow.draw_type = datarow.draw;
			if (datarow.draw.match("^LINE[0-9]$")) datarow.draw_type = 'line';
			if (datarow.draw == 'AREA' || datarow.draw == 'STACK') datarow.draw_type = "area";
			if (datarow.draw == 'AREASTACK') datarow.draw_type = "areastack";
			if (datarow.draw.match("^LINESTACK[0-9]$")) datarow.draw_type = "linestack";

			datarow.stack = datarow.draw_type == 'area' || datarow.draw_type == 'areastack' || datarow.draw_type == 'linestack';

			datarow.values = $.map(values, function(row) {
				return {
					date: new Date(row[0]),
					value: row[1][name],
					y: row[1][name], // required for stacking
				}
			});

			l.push(datarow);
		});

		l.sort(function(a, b) {
			var i = graph_order.indexOf(a.name);
			var j = graph_order.indexOf(b.name);

			return i == j ? 0 : ((i < j) ? -1 : 1);
		});

		return l;
	}();

	this.get = function(name) {
		for (var i=0; i < this.all.length; i++) {
			if (this.all[i].name == name) return this.all[i];
		}
	}

	this.names = graph_order;

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

    this.range_start = function() {
        var start = this.container.data('range-start');
        return start ? Math.round(start / 1000, 0) : start;
    }
    this.range_end = function() {
        var end = this.container.data('range-end');
        return end ? Math.round(end / 1000, 0) : end;
    }

	// time scale over the whole width of our area
	this.xScale = d3.time.scale().range([0, this.width]);

	this.xAxisNumTicks = {
		'day': this.numXAxisTicks,
		'week': 7,
		'month': this.numXAxisTicks,
		'year': 12,
		'custom': this.numXAxisTicks,
	}

	this.xAxisTickFormats = {
		'day': d3.time.format("%H:%M"),
		'week': d3.time.format("%d"),
		'month': d3.time.format("Week %U"),
		'year': d3.time.format("%b"),
		'custom': d3.time.format("%H:%M"),
	}

	// x axis definition
	this.xAxis = d3.svg.axis()
					.scale(this.xScale)
					.orient("bottom")
					.innerTickSize(-this.height)
					.outerTickSize(0) // remove tick marker at min/max
					.ticks(this.xAxisNumTicks[this.scope])
					.tickFormat(this.scope != "custom" ? this.xAxisTickFormats[this.scope] : undefined);

	// linear scale over the complete height
	this.yScale = d3.scale.linear().range([this.height, 0]);

	// SI unit format for y axis. TODO: Is this always good?
	this.yAxisTickFormat = d3.format("s");

	// y axis definition
	this.yAxis = d3.svg.axis().scale(this.yScale)
					.orient("left")
					.innerTickSize(-this.width)
					.outerTickSize(0)  // remove tick marker at min/max
					.ticks(this.numYAxisTicks)
					.tickFormat(this.yAxisTickFormat);

	// definition for every line in our graphs
	this.line = d3.svg.line().interpolate("basis")
		.defined(function(d) { return d.value != null; }) // makes null values a gap
		.x(function(d) { return this.xScale(d.date); }) // convert all values for x and y in our data to a px value in our svg
		.y(function(d) { return this.yScale(d.value); });

	// definition for areas in our graphs
	this.area = d3.svg.area()
		.defined(function(d) { return d.value != null; }) // makes null values a gap
		.x(function(d) { return this.xScale(d.date); })
		.y0(function(d) { return this.yScale(d.y0 || 0) })
		.y1(function(d) { return this.yScale((d.y0 || 0) + d.value); });

	// format for items in the legend table. .2 means two decimal points
	this.legendFormat = d3.format('.2s')

	// stack layout definition
	this.stack = d3.layout.stack().values(function(d) { return d.values; });

	this.render = function() {
		//this.debug("Rendering " + this.scope + " in " + this.container + " with data from " + this.url);

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
			type: 'get',
			data: {
			    'start': this.range_start(),
			    'end': this.range_end(),
			},
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
		this.color = d3.scale.category20().domain(this.datarows.names);

		// setup the x axis of the graph
		this.xScale.domain(d3.extent(this.datarows.dates));

		// add the x axis to the graph object
		this.svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + this.height + ")")
		  	.call(this.xAxis);

        // move x axis label to the center of the tick area
        if (this.scope != "day" && this.scope != "custom") {
            this.svg.selectAll('.x text').attr('transform', 'translate(' + (this.width / this.xAxisNumTicks[this.scope] / 2) + ', 0)');
        }

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

		$.each(this.draw_groups(this.datarows.all), function(idx, data) {
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

		this.datarows = new Datarows(response.datarows, response.yaxis.graph_order, response.values);
	}

	// creates an array of array used for passing to d3.js
	//
	// each array in the array contains one or more datarows to draw together.
	// the datarows are grouped by the draw_type property which is a more high-level description of the actual
	// .draw property.
	// The datarows are grouped together like this:
	// - AREA + STACK
	// - AREASTACK
	// - LINESTACK(1|2|3)
	// - LINE(1|2|3)
	this.draw_groups = function(all_datarows) {
		var groups = [];

		var last_draw_type = "";
		var last_draw_stack = null;

		var current_group = [];

		for (var i=0; i < all_datarows.length; i++) {
			var current_datarow = all_datarows[i];

			if (current_datarow.draw_type != last_draw_type) {

				if (current_group.length) {
					if (last_draw_stack === true) {
						groups.push(this.stack(current_group));
					} else {
						groups.push(current_group);
					}

					current_group = [];
				}
			}
			current_group.push(current_datarow);

			last_draw_type = current_datarow.draw_type;
			last_draw_stack = current_datarow.stack;
		}

		if (current_group.length) {
			if (last_draw_stack === true) {
				groups.push(this.stack(current_group));
			} else {
				groups.push(current_group);
			}
		}

		return groups;
	}

	// helper function to get the color for a datarows. This is either the value from the datarow config
	// or the value from the color() definition
	this.getColor = function(d) {
		return d.color || this.color(d.sameas || d.name);
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
		var groups = [];

		for (var i=0; i < this.datarows.all.length; i++) {
			var datarow = this.datarows.all[i];
			if (datarow.sameas) {
				for (var j=0; j < groups.length; j++) {
					if (groups[j][0].name == datarow.sameas) {
						groups[j].push(datarow);
						break;
					}
				}
			} else {
				groups.push([datarow]);
			}
		}

		for (var i=0; i < groups.length; i++) {
			var group = groups[i];
			var primary_datarow = group[0];
			var label = primary_datarow.label || primary_datarow.name;

			var scale_sides = $.map(group, function(dr, x) { return dr.sameas ? '+' : '-'; });
			var min_values = $.map(group, function(dr, x) { return dr.value_min ? graph.legendFormat(dr.value_min) : '-'; });
			var max_values = $.map(group, function(dr, x) { return dr.value_max ? graph.legendFormat(dr.value_max) : '-'; });
			var current_values = $.map(group, function(dr, x) { return dr.value_current ? graph.legendFormat(dr.value_current) : '-'; });
			var group_names = $.map(group, function(dr, x) { return dr.name; });

			var tr = $('<tr></tr>')
						.attr('data-datarow', primary_datarow.name)
						.attr('data-datarow-names', group_names.join(' '))
						.append($('<td></td>').append(
							$('<span class="color"></span>')
								.attr('style', 'background-color: ' + this.getColor(primary_datarow))
						))
						.append($('<td class="small"></td>')
									.text(label + (scale_sides.length > 1 ? ' (' + scale_sides.join('/') + ')' : ''))
									.attr('title', primary_datarow.info || label)
						)
						.append($('<td class="small"></td>').text(min_values.join(' / ')))
						.append($('<td class="small"></td>').text(max_values.join(' / ')))
						.append($('<td class="small"></td>').text(current_values.join(' / ')));

			tr.hover(function() {
				var highlight_datarows = $(this).data('datarow-names').split(' ');
				for (var i=0; i < highlight_datarows.length; i++) {
					$('svg path[data-datarow=' + highlight_datarows[i] + ']', graph.container).addClass('highlighted');
				}
			}, function() {
				$('svg path', graph.container).removeClass('highlighted');
			});

			legend.append(tr);
		};

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

    function insert_graph(graph_div) {
    	var url = $(graph_div).data('url');
		if (!url) return;

		var g = new DjuninGraph('#' + graph_div.id, url);
		g.render();
		return g;
    }

    // auto-load graphs for day, week, month, year
	$('.djunin-graph:visible').each(function(i, elem) { insert_graph(elem); });

    // event handler for custom range graph
	$('#graph-custom').on('shown.bs.modal', function() {
	    $('svg,table', $(this)).remove();
	    var elem = $('.djunin-graph', this)[0];
	    if (!$(elem).data('range-start')) {
	        $(elem).data('range-start', new Date().getTime() - (34*3600*1000)); // mimic -34h from graphs.py
	    }
	    if (!$(elem).data('range-end')) {
	        $(elem).data('range-end', new Date().getTime());
	    }
	    insert_graph(elem);
	});

	// todo: this creates a new svg object every time!
	$('#custom-zoom-out').on('click', function() {
		var div = $('#graph-custom .djunin-graph')[0];
	    var x = $(div);
	    var start = x.data('range-start');
	    var end = x.data('range-end');
	    var diff = end - start;
	    var new_range = diff * 2;

	    x.data('range-start', start - (new_range/2));
	    x.data('range-end', end + (new_range/2));

		$('svg,table', x.parent()).remove();
	    insert_graph(div);
	});

	// todo: this creates a new svg object every time!
	$('#custom-zoom-in').on('click', function() {
		var div = $('#graph-custom .djunin-graph')[0];
	    var x = $(div);
	    var start = x.data('range-start');
	    var end = x.data('range-end');
	    var diff = end - start;
	    var new_range = diff / 2;

	    x.data('range-start', start + (new_range/2));
	    x.data('range-end', end - (new_range/2));

		$('svg,table', x.parent()).remove();
	    insert_graph(div);
	});
});
