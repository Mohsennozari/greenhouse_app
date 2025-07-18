document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.chart-iframe').forEach(iframe => {
        iframe.onload = function() {
            const chart = iframe.contentWindow.Plotly;
            if (chart) {
                const plotDiv = iframe.contentWindow.document.querySelector('.plotly-graph-div');
                chart.register(iframe.contentWindow.Plotly);
                plotDiv.on('plotly_click', function(data) {
                    const point = data.points[0];
                    alert(`زمان: ${point.x}\nمقدار: ${point.y}`);
                });
            }
        };
    });
});