/* ============================================================
   Quiz Master Pro - Quiz JavaScript
   Loads attempt state, renders questions, handles timer,
   palette, autosave, auto-submit and final submission.
   ============================================================ */

(function () {
    'use strict';

    const QMP = window.QMP;
    const $ = QMP.$;

    const dataBox = $('#quizData');
    const questionCount = parseInt(dataBox.dataset.questionCount, 10);
    const duration = parseInt(dataBox.dataset.duration, 10);

    let state = null;               // { questions, answers, remaining }
    let currentIndex = 0;
    let timerHandle = null;
    let submitting = false;

    const OPT_LETTERS = ['A', 'B', 'C', 'D'];

    /* ---------------- Initial load ---------------- */
    async function loadState() {
        const res = await fetch('/quiz/state', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await res.json();
        if (!res.ok) {
            window.location.href = '/categories';
            return;
        }
        if (data.submitted) {
            window.location.href = '/result/' + data.result_id;
            return;
        }
        state = data;
        buildPalette();
        renderQuestion();
        startTimer(state.remaining || 0);
    }

    /* ---------------- Rendering ---------------- */
    function buildPalette() {
        const grid = $('#paletteGrid');
        grid.innerHTML = '';
        for (let i = 0; i < questionCount; i++) {
            const btn = document.createElement('button');
            btn.className = 'palette-btn';
            btn.textContent = i + 1;
            btn.addEventListener('click', () => goto(i));
            grid.appendChild(btn);
        }
    }

    function currentQuestion() {
        return state.questions[currentIndex];
    }

    function renderQuestion() {
        const q = currentQuestion();
        const answered = state.answers[currentIndex];

        $('#qNum').textContent = currentIndex + 1;
        $('#qText').textContent = q.question;

        const box = $('#options');
        box.innerHTML = '';
        q.options.forEach((opt, i) => {
            const label = document.createElement('div');
            label.className = 'option' + (answered === i ? ' selected' : '');
            label.innerHTML =
                `<span class="opt-letter">${OPT_LETTERS[i]}</span>
                 <span>${QMP.escapeHtml(opt)}</span>`;
            label.addEventListener('click', () => selectAnswer(i));
            box.appendChild(label);
        });

        $('#prevBtn').disabled = currentIndex === 0;
        const nextBtn = $('#nextBtn');
        nextBtn.innerHTML = currentIndex === questionCount - 1
            ? '<i class="fa-solid fa-paper-plane"></i> Submit'
            : 'Next <i class="fa-solid fa-arrow-right"></i>';

        updatePalette();
        updateProgress();
    }

    function updatePalette() {
        $$('#paletteGrid .palette-btn').forEach((btn, i) => {
            btn.className = 'palette-btn';
            if (i === currentIndex) btn.classList.add('current');
            if (state.answers[i] !== undefined) btn.classList.add('answered');
        });
    }

    function updateProgress() {
        const answered = Object.keys(state.answers).filter(k => state.answers[k] !== undefined).length;
        $('#answeredCount').textContent = answered;
        $('#qpFill').style.width = ((answered / questionCount) * 100) + '%';
    }

    /* ---------------- Answer selection + autosave ---------------- */
    async function selectAnswer(i) {
        const q = currentQuestion();
        const prev = state.answers[currentIndex];
        const wasAnswered = prev !== undefined;

        state.answers[currentIndex] = i;
        renderQuestion();

        // Sound feedback: only when actually changing the answer.
        if (!wasAnswered) QMP.playClick();

        try {
            await QMP.apiFetch('/quiz/answer', {
                method: 'POST',
                body: { q_index: currentIndex, selected: i },
            });
        } catch (err) {
            console.error('Autosave failed:', err.message);
        }
    }

    /* ---------------- Navigation ---------------- */
    function goto(i) {
        if (i < 0 || i >= questionCount) return;
        currentIndex = i;
        renderQuestion();
        $('#qText').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    $('#prevBtn').addEventListener('click', () => goto(currentIndex - 1));
    $('#nextBtn').addEventListener('click', () => {
        if (currentIndex === questionCount - 1) {
            openSubmitConfirm();
        } else {
            goto(currentIndex + 1);
        }
    });

    document.addEventListener('keydown', e => {
        if (e.target.tagName === 'INPUT') return;
        if (e.key === 'ArrowRight') goto(currentIndex + 1);
        if (e.key === 'ArrowLeft') goto(currentIndex - 1);
        if (e.key >= '1' && e.key <= '4') selectAnswer(parseInt(e.key, 10) - 1);
    });

    /* ---------------- Timer ---------------- */
    function startTimer(seconds) {
        let remaining = seconds;
        const timerText = $('#timerText');
        const timerBox = $('#timerBox');
        updateTimerUI(remaining);

        timerHandle = setInterval(() => {
            remaining -= 1;
            updateTimerUI(remaining);
            if (remaining <= 0) {
                clearInterval(timerHandle);
                autoSubmit();
            }
        }, 1000);
    }

    function updateTimerUI(seconds) {
        const timerText = $('#timerText');
        const timerBox = $('#timerBox');
        timerText.textContent = QMP.formatTime(seconds);
        timerBox.classList.toggle('low', seconds <= 60);
        if (seconds <= 10) timerBox.classList.add('low');
    }

    /* ---------------- Submission ---------------- */
    function openSubmitConfirm() {
        const answered = Object.keys(state.answers).filter(k => state.answers[k] !== undefined).length;
        const missing = questionCount - answered;
        $('#confirmText').innerHTML = missing > 0
            ? `<strong>${missing}</strong> question${missing > 1 ? 's' : ''} unanswered. Submit anyway?`
            : 'All questions answered. Ready to submit?';
        $('#submitModal').classList.add('open');
    }

    $('#submitBtnMain').addEventListener('click', openSubmitConfirm);
    $('#confirmSubmitBtn').addEventListener('click', () => {
        $('#submitModal').classList.remove('open');
        doSubmit();
    });

    async function autoSubmit() {
        if (submitting) return;
        $('#submitModal').classList.remove('open');
        await doSubmit();
    }

    async function doSubmit() {
        if (submitting) return;
        submitting = true;
        try {
            const res = await QMP.apiFetch('/quiz/submit', { method: 'POST' });
            window.location.href = '/result/' + res.result_id;
        } catch (err) {
            console.error('Submit failed:', err.message);
            submitting = false;
        }
    }

    /* ---------------- Fullscreen ---------------- */
    $('#fullscreenBtn').addEventListener('click', () => {
        if (document.fullscreenElement) {
            document.exitFullscreen();
            $('#fullscreenBtn i').className = 'fa-solid fa-expand';
        } else {
            document.documentElement.requestFullscreen().catch(() => {});
            $('#fullscreenBtn i').className = 'fa-solid fa-compress';
        }
    });
    document.addEventListener('fullscreenchange', () => {
        $('#fullscreenBtn i').className = document.fullscreenElement ? 'fa-solid fa-compress' : 'fa-solid fa-expand';
    });

    /* ---------------- Boot ---------------- */
    loadState();
})();
