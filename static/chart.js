document.addEventListener('DOMContentLoaded', function() {
    // انیمیشن لودینگ
    function showLoading() {
        const loading = document.getElementById('loading');
        loading.style.display = 'flex';
        const timeout = setTimeout(() => {
            loading.style.display = 'none';
        }, 5000);

        fetch('/check_processing_status')
            .then(response => response.json())
            .then(data => {
                clearTimeout(timeout);
                loading.style.display = 'none';
                if (data.status === 'complete' && data.latest) {
                    updateStatus(data.latest);
                }
            })
            .catch(() => {
                clearTimeout(timeout);
                loading.style.display = 'none';
                alert('خطا در ارتباط با سرور');
            });
    }

    // به‌روزرسانی وضعیت فعلی
    function updateStatus(latest) {
        const statusItems = [
            {
                id: 'temperature',
                value: latest.temperature,
                alert: latest.temperature_alert,
                distance: latest.temp_distance,
                confidence: latest.temp_confidence
            },
            {
                id: 'humidity',
                value: latest.humidity,
                alert: latest.humidity_alert,
                distance: latest.hum_distance,
                confidence: latest.hum_confidence
            },
            {
                id: 'light',
                value: latest.light,
                alert: latest.light_alert,
                distance: latest.light_distance,
                confidence: latest.light_confidence
            }
        ];

        statusItems.forEach(item => {
            const element = document.querySelector(`.status-item.status-${item.id}`);
            if (element) {
                element.querySelector('p:nth-child(2)').textContent = item.value.toFixed(2);
                element.querySelector('p:nth-child(3)').textContent = item.alert ? 'نیاز به بررسی' : 'نرمال';
                element.querySelector('p:nth-child(4)').textContent = `فاصله از نقطه بحران: ${item.distance.toFixed(2)} ${item.id === 'temperature' ? '°C' : item.id === 'humidity' ? '%' : 'Lux'}`;
                element.querySelector('.progress').style.width = `${item.confidence}%`;
                element.querySelector('p:nth-child(6)').textContent = `درصد اطمینان: ${item.confidence.toFixed(2)}%`;
                element.className = `status-item status-${item.alert ? 'danger' : 'success'} status-${item.id}`;
            }
        });
    }

    // مدیریت نوتیفیکیشن‌ها
    const notification = document.querySelector('.notification');
    if (notification) {
        setTimeout(() => {
            notification.classList.add('hide');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }

    // اعتبارسنجی فرم تنظیم آستانه‌ها
    const thresholdForm = document.querySelector('form[action="/update_thresholds"]');
    if (thresholdForm) {
        thresholdForm.addEventListener('submit', function(event) {
            const inputs = thresholdForm.querySelectorAll('input[type="number"]');
            let valid = true;
            inputs.forEach(input => {
                const value = parseFloat(input.value);
                const min = parseFloat(input.min);
                const max = parseFloat(input.max);
                if (isNaN(value) || value < min || value > max) {
                    valid = false;
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });
            if (!valid) {
                event.preventDefault();
                alert('لطفاً مقادیر معتبر برای آستانه‌ها وارد کنید.');
            }
        });
    }

    // مرتب‌سازی جدول
    const table = document.getElementById('dataTable');
    if (table) {
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                const isNumeric = column !== 'datetime';
                const ascending = header.classList.toggle('asc');

                rows.sort((a, b) => {
                    let aValue = a.cells[header.cellIndex].textContent;
                    let bValue = b.cells[header.cellIndex].textContent;

                    if (isNumeric) {
                        aValue = parseFloat(aValue) || 0;
                        bValue = parseFloat(bValue) || 0;
                    } else {
                        aValue = new Date(aValue);
                        bValue = new Date(bValue);
                    }

                    return ascending ? (aValue > bValue ? 1 : -1) : (aValue < bValue ? 1 : -1);
                });

                const tbody = table.querySelector('tbody');
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    }

    // مدیریت تمام‌صفحه برای بخش‌ها
    document.querySelectorAll('.fullscreen-btn[data-section]').forEach(btn => {
        btn.addEventListener('click', () => {
            const sectionId = btn.dataset.section;
            const section = document.querySelector(`.card[data-section="${sectionId}"]`);

            if (!document.fullscreenElement) {
                section.classList.add('fullscreen');
                if (section.requestFullscreen) {
                    section.requestFullscreen().catch(err => console.error('Fullscreen error:', err));
                }
            } else {
                section.classList.remove('fullscreen');
                if (document.exitFullscreen) {
                    document.exitFullscreen().catch(err => console.error('Exit fullscreen error:', err));
                }
            }
        });
    });

    // مدیریت تمام‌صفحه برای نمودارها
    document.querySelectorAll('.fullscreen-btn[data-chart]').forEach(btn => {
        btn.addEventListener('click', () => {
            const chartId = btn.dataset.chart;
            const chart = btn.closest('.chart');

            if (!document.fullscreenElement) {
                chart.classList.add('fullscreen');
                if (chart.requestFullscreen) {
                    chart.requestFullscreen().catch(err => console.error('Fullscreen error:', err));
                }
            } else {
                chart.classList.remove('fullscreen');
                if (document.exitFullscreen) {
                    document.exitFullscreen().catch(err => console.error('Exit fullscreen error:', err));
                }
            }
        });
    });

    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            document.querySelectorAll('.card, .chart').forEach(el => {
                el.classList.remove('fullscreen');
            });
        }
    });

    // مدیریت انتخاب فرمت تاریخ
    window.updateDateFormat = function() {
        const dateFormat = document.getElementById('date-format').value;
        window.location.href = `/?date_format=${dateFormat}`;
    };

    // به‌روزرسانی بلادرنگ
    setInterval(() => {
        fetch('/check_processing_status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'complete' && data.latest) {
                    updateStatus(data.latest);
                }
            })
            .catch(() => console.error('Error fetching real-time data'));
    }, 60000);

    // لودینگ اولیه
    showLoading();
});