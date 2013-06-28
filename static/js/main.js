function initSvg() {
    'use strict';

    var $svg = $('svg');

    var zoomIn = function(factor) {
        $svg.width($svg.width() * factor);
        $svg.height($svg.height() * factor);
    };

    var zoomOut = function(factor) {
        $svg.width($svg.width() / factor);
        $svg.height($svg.height() / factor);
    };

    $('#zoomOut').on('click', zoomOut.bind(this, 1.5));
    $('#zoomIn').on('click', zoomIn.bind(this, 1.5));

    $svg.on('mousewheel', function(e) {
        var $window = $(window);
        var windowCenterX = $window.width() / 2,
            windowCenterY = $window.height() / 2;

        var event = e.originalEvent;

        scrollBy(event.clientX - windowCenterX, event.clientY - windowCenterY);

        if (event.wheelDelta > 0) {
            zoomIn(1.1);
        } else {
            zoomOut(1.1);
        }
    });

    zoomOut($svg.width() / $(window).width());
}

function highlightEdge(edge) {
    'use strict';

    window.highlightedEdges.push(edge);
    edge.path.attr('stroke-width', '7px');
    edge.path.attr('stroke', 'red');
}

function highlight(elem, c) {
    'use strict';

    var color = c || '#00ffff';
    window.highlighted.push(elem);
    elem.ellipse.css('fill', color);
    elem.children.forEach(function(el) {
        highlight(el);
    });

    elem.outEdges.forEach(highlightEdge.bind(this));
}


function unHighlightAll() {
    'use strict';

    window.highlighted.forEach(function(el) {
        el.ellipse.css('fill', 'white');
    }.bind(this));

    window.highlighted = [];

    window.highlightedEdges.forEach(function(edge) {
        edge.path.attr('stroke-width', '');
        edge.path.attr('stroke', 'black');
    }.bind(this));

    window.highlightedEdges = [];
}


function highlightClick(elem, e) {
    'use strict';

    unHighlightAll();
    highlight(elem, 'gray');
}


function loadSvg(name) {
    'use strict';

    window.nodes = {};
    window.edges = {};
    window.highlighted = [];
    window.highlightedEdges = [];

    var $container = $('#container');
    $container.empty();

    $.ajax({url: '/svg',
        data: {file: name},
        success: function(response) {
            $('g', response.documentElement).each(function(index, el) {
                var text = $('title', el).text();
                var className = el.className.baseVal;

                if (className === 'node') {
                    var elem = window.nodes[text] = window.nodes[text] || {};

                    elem.type = 'node';
                    elem.element = el;
                    elem.$element = $(el);
                    elem.inEdges = [];
                    elem.outEdges = [];
                    elem.ellipse = $('ellipse', el);
                    elem.children = [];

                    elem.$element.on('click', highlightClick.bind(this, elem));

                } else if (className === 'edge') {
                    var splited = text.split('--');

                    var nodeFrom = window.nodes[splited[0]] = window.nodes[splited[0]] || {children: [], inEdges: [], outEdges: []};
                    var nodeTo = window.nodes[splited[1]] = window.nodes[splited[1]] || {children: [], inEdges: [], outEdges: []};

                    var edge = window.edges[text] = window.edges[text] || {};
                    edge.type = 'edge';
                    edge.path = $('path', el);
                    edge.element = el;

                    nodeFrom.children.push(nodeTo);
                    nodeFrom.outEdges.push(edge);
                    nodeTo.inEdges.push(edge);
                }

                unHighlightAll();
            });

            $('#container').append(response.documentElement);
            initSvg();
        }.bind(this)
    });

}

$(document).ready(function() {
    'use strict';

    loadSvg();

    var $input = $('#filename');

    function onSuccess(res) {
        $input.autocomplete({source: res});
    }

    function getSuggest() {
        var value = $input.val();
        if (!value || value.length < 2) return;

        $.ajax({
            url: '/file_suggest',
            data: {'name': $input.val()},
            dataType: 'json',
            success: onSuccess
        });
    }

    $input.bind('keyup', getSuggest);

    var $getSvgButton = $('#getSvg');

    $getSvgButton.on('click', function() {
        var name = $input.val();
        if (!name) { return; }
        loadSvg(name);
    }.bind(this));
});

