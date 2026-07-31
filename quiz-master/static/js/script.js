/* ============================================================
   Quiz Master Pro - Global JavaScript
   Theme, loader, nav, UI helpers, CSRF + fetch wrappers, sounds.
   ============================================================ */

(function () {
    'use strict';

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

    /* ---------------- Theme ----------------- */
    const THEME_KEY = 'qmp-theme';

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const icon = $('#themeToggle i');
        if (icon) icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }

    function initTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(saved || (prefersDark ? 'dark' : 'light'));
        const btn = $('#themeToggle');
        if (btn) {
            btn.addEventListener('click', () => {
                const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                localStorage.setItem(THEME_KEY, next);
                applyTheme(next);
            });
        }
    }

    /* ---------------- Loader ----------------- */
    function initLoader() {
        const loader = $('#loader');
        if (!loader) return;
        window.addEventListener('load', () => loader.classList.add('hidden'));
        // Safety fallback so the loader never blocks the page.
        setTimeout(() => loader.classList.add('hidden'), 2500);
    }

    /* ---------------- Navbar ----------------- */
    function initNav() {
        const burger = $('#hamburger');
        const links = $('#navLinks');
        if (burger && links) {
            burger.addEventListener('click', () => links.classList.toggle('open'));
            $$('#navLinks a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
        }
    }

    /* ---------------- Flash dismiss ----------------- */
    function initFlashes() {
        $$('.flash-close').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.flash').style.opacity = '0';
                setTimeout(() => btn.closest('.flash').remove(), 250);
            });
        });
        // Auto-dismiss success/info flashes after 5s.
        setTimeout(() => {
            $$('.flash-success, .flash-info').forEach(f => {
                f.style.transition = 'opacity 0.5s';
                f.style.opacity = '0';
                setTimeout(() => f.remove(), 600);
            });
        }, 5000);
    }

    /* ---------------- Scroll reveal ----------------- */
    function initReveal() {
        const els = $$('.fade-up');
        if (!('IntersectionObserver' in window) || !els.length) {
            els.forEach(el => el.classList.add('visible'));
            return;
        }
        const io = new IntersectionObserver(entries => {
            entries.forEach(e => {
                if (e.isIntersecting) {
                    e.target.classList.add('visible');
                    io.unobserve(e.target);
                }
            });
        }, { threshold: 0.12 });
        els.forEach(el => io.observe(el));
    }

    /* ---------------- Password visibility toggle ----------------- */
    function initPasswordToggles() {
        $$('.toggle-pass').forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.closest('.input-wrapper').querySelector('input');
                const show = input.type === 'password';
                input.type = show ? 'text' : 'password';
                btn.innerHTML = show ? '<i class="fa-solid fa-eye-slash"></i>' : '<i class="fa-solid fa-eye"></i>';
            });
        });
    }

    /* ---------------- Modals ----------------- */
    window.openModal = function (id) {
        const el = document.getElementById(id);
        if (el) el.classList.add('open');
    };
    window.closeModal = function (id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove('open');
    };
    function initModals() {
        $$('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', e => {
                if (e.target === overlay) overlay.classList.remove('open');
            });
        });
        $$('[data-close-modal]').forEach(btn => {
            btn.addEventListener('click', () => {
                const overlay = btn.closest('.modal-overlay');
                if (overlay) overlay.classList.remove('open');
            });
        });
    }

    /* ---------------- CSRF + fetch wrapper ----------------- */
    function csrfToken() {
        const meta = $('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    async function apiFetch(url, options = {}) {
        const opts = options || {};
        opts.headers = Object.assign(
            { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRF-Token': csrfToken() },
            opts.headers || {}
        );
        if (opts.body && typeof opts.body !== 'string') {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(opts.body);
        }
        const res = await fetch(url, opts);
        const contentType = res.headers.get('content-type') || '';
        let data = null;
        if (contentType.includes('application/json')) {
            data = await res.json().catch(() => null);
        } else {
            data = await res.text();
        }
        if (!res.ok) throw new Error((data && data.error) || `Request failed (${res.status})`);
        return data;
    }

    window.QMP = {
        $,
        $$,
        csrfToken,
        apiFetch,
        formatTime(seconds) {
            seconds = Math.max(0, Math.floor(seconds));
            const m = Math.floor(seconds / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            return `${m}:${s}`;
        },
        escapeHtml(str) {
            const div = document.createElement('div');
            div.textContent = str == null ? '' : String(str);
            return div.innerHTML;
        },
    };

    /* ---------------- Sound effects (Web Audio) ----------------- */
    let audioCtx = null;
    function ensureAudio() {
        if (!audioCtx) {
            const AC = window.AudioContext || window.webkitAudioContext;
            if (AC) audioCtx = new AC();
        }
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        return audioCtx;
    }
    function playTone(freq, duration, type, volume, when) {
        const ctx = ensureAudio();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || 'sine';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0, ctx.currentTime + (when || 0));
        gain.gain.linearRampToValueAtTime(volume || 0.18, ctx.currentTime + (when || 0) + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + (when || 0) + duration);
        osc.connect(gain).connect(ctx.destination);
        osc.start(ctx.currentTime + (when || 0));
        osc.stop(ctx.currentTime + (when || 0) + duration + 0.05);
    }
    window.QMP.playCorrect = function () {
        playTone(660, 0.12, 'sine', 0.2);
        playTone(880, 0.18, 'sine', 0.2, 0.1);
    };
    window.QMP.playWrong = function () {
        playTone(220, 0.25, 'triangle', 0.2);
        playTone(160, 0.28, 'triangle', 0.2, 0.12);
    };
    window.QMP.playClick = function () {
        playTone(500, 0.06, 'square', 0.06);
    };
    window.QMP.playWin = function () {
        [523, 659, 784, 1047].forEach((f, i) => playTone(f, 0.22, 'sine', 0.2, i * 0.12));
    };
    window.QMP.playLose = function () {
        [392, 330, 262].forEach((f, i) => playTone(f, 0.3, 'triangle', 0.18, i * 0.16));
    };

    /* ---------------- Boot ----------------- */
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        initLoader();
        initNav();
        initFlashes();
        initReveal();
        initPasswordToggles();
        initModals();
    });
})();
