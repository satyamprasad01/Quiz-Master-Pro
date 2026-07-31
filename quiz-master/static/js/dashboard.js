/* ============================================================
   Quiz Master Pro - Dashboard JavaScript
   Loads user stats via AJAX and renders Chart.js charts + badges.
   ============================================================ */

(function () {
    'use strict';

    const QMP = window.QMP;
    const $ = QMP.$;

    // Chart.js default colour handling for light/dark themes.
    function textColor() {
        return document.documentElement.getAttribute('data-theme') === 'dark' ? '#e8e8ff' : '#1e1b4b';
    }
    const gridColor = () => 'rgba(99,102,241,0.12)';

    const GRAD = ['#6366f1', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#3b82f6'];

    function buildCharts(stats) {
        if (!window.Chart) return;

        Chart.defaults.font.family = "'Poppins', sans-serif";
        Chart.defaults.color = textColor();

        // Attempts over time
        const attemptsCtx = $('#attemptsChart');
        if (attemptsCtx && stats.attempts_over_time) {
            const { labels, values } = stats.attempts_over_time;
            new Chart(attemptsCtx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Attempts',
                        data: values,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139,92,246,0.15)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#a855f7',
                        pointRadius: 4,
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: gridColor() } },
                        y: { beginAtZero: true, grid: { color: gridColor() }, ticks: { precision: 0 } },
                    },
                },
            });
        }

        // Category average
        const catCtx = $('#categoryChart');
        if (catCtx && stats.category_avg && stats.category_avg.labels.length) {
            new Chart(catCtx, {
                type: 'doughnut',
                data: {
                    labels: stats.category_avg.labels,
                    datasets: [{
                        data: stats.category_avg.values,
                        backgroundColor: GRAD,
                        borderWidth: 0,
                        hoverOffset: 8,
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    cutout: '62%',
                    plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } },
                },
            });
        }

        // Score trend
        const trendCtx = $('#trendChart');
        if (trendCtx && stats.score_trend && stats.score_trend.labels.length) {
            new Chart(trendCtx, {
                type: 'bar',
                data: {
                    labels: stats.score_trend.labels,
                    datasets: [{
                        label: 'Score %',
                        data: stats.score_trend.values,
                        backgroundColor: stats.score_trend.values.map(v => v >= 60 ? 'rgba(16,185,129,0.75)' : 'rgba(239,68,68,0.75)'),
                        borderRadius: 8,
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: gridColor() } },
                        y: { beginAtZero: true, max: 100, grid: { color: gridColor() } },
                    },
                },
            });
        }
    }

    function renderBadges(badges) {
        const box = $('#badgesBox');
        if (!box) return;
        if (!badges.length) {
            box.innerHTML = '<p class="muted">No badges yet. Play quizzes to earn achievements!</p>';
            return;
        }
        box.innerHTML = badges.map(b =>
            `<div class="badge-chip"><i class="fa-solid ${b.icon}"></i><span><strong>${QMP.escapeHtml(b.name)}</strong> — ${QMP.escapeHtml(b.desc)}</span></div>`
        ).join('');
    }

    document.addEventListener('DOMContentLoaded', () => {
        QMP.apiFetch('/api/user/stats')
            .then(stats => buildCharts(stats))
            .catch(err => console.error('Failed to load stats:', err.message));

        QMP.apiFetch('/api/achievements')
            .then(renderBadges)
            .catch(err => console.error('Failed to load badges:', err.message));
    });
})();
