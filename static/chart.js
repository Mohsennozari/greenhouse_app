$(document).ready(function() {
    // لودینگ اولیه
    setTimeout(() => $('#loading').hide(), 2000);

    // تنظیم جدول
    $('#dataTable').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/fa.json' },
        pageLength: 10,
        order: [[0, 'desc']],
        scrollY: '35vh',
        scrollX: true,
        scrollCollapse: true,
        fixedHeader: true,
        searching: false,
        columnDefs: [
            { targets: '_all', className: 'dt-center' },
            { width: '20%', targets: 0 },
            { width: '20%', targets: 1 },
            { width: '20%', targets: 2 },
            { width: '20%', targets: 3 },
            { width: '20%', targets: 4 }
        ],
        responsive: true
    });

    // انیمیشن لودینگ
    function showLoading() {
        $('#loading').css('display', 'flex');
        let width = 0;
        const progressBar = $('#progress-bar');
        const interval = setInterval(() => {
            width += 100 / (3 * 20);
            progressBar.css('width', width + '%').attr('aria-valuenow', width);
            if (width >= 100) clearInterval(interval);
        }, 50);

        $.ajax({
            url: '/check_processing_status',
            success: function(response) {
                if (response.status === 'complete') {
                    $('#loading').hide();
                }
            },
            complete: function() {
                setTimeout(() => $('#loading').hide(), 3000);
            }
        });
    }

    // رفرش خودکار هر 5 دقیقه
    setTimeout(function() {
        showLoading();
        window.location.reload();
    }, 300000);

    // مدیریت تمام‌صفحه
    $('.fullscreen-btn, .chart-container').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const sectionId = $(this).data('section') || $(this).closest('.fullscreen-section').data('section');
        const section = $(`.fullscreen-section[data-section="${sectionId}"]`)[0];

        if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
            if (section.requestFullscreen) {
                section.requestFullscreen().catch(err => console.error('Fullscreen error:', err));
            } else if (section.webkitRequestFullscreen) {
                section.webkitRequestFullscreen();
            } else if (section.msRequestFullscreen) {
                section.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen().catch(err => console.error('Exit fullscreen error:', err));
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
    });

    // مدیریت وضعیت تمام‌صفحه
    $(document).on('fullscreenchange webkitfullscreenchange msfullscreenchange', function() {
        if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
            $('.fullscreen-section').removeClass('fullscreen');
        } else {
            $('.fullscreen-section').addClass('fullscreen');
        }
    });
});
