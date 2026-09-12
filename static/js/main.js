/**
 * NeuroScan AI — Clinical Workstation Frontend
 * Theme toggle, dynamic greeting, dropzone, modal, analysis processing state, flash auto-dismiss
 */

/* ─── Theme Toggle ──────────────────────────────────────────────── */

const THEME_KEY = 'ns-theme';

function getTheme() {
    try { return localStorage.getItem(THEME_KEY) || 'light'; } catch (e) { return 'light'; }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
}

function initThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;

    btn.setAttribute('aria-pressed', getTheme() === 'dark' ? 'true' : 'false');

    btn.addEventListener('click', () => {
        const next = getTheme() === 'light' ? 'dark' : 'light';
        applyTheme(next);
        btn.setAttribute('aria-pressed', next === 'dark' ? 'true' : 'false');
    });
}

/* ─── Dynamic Time-of-Day Greeting ─────────────────────────────── */

function initGreeting() {
    const el = document.getElementById('heroGreeting');
    if (!el) return;
    const name = el.getAttribute('data-name') || '';
    const h = new Date().getHours();
    const salutation = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
    el.textContent = `${salutation}, ${name}`;
}

/* ─── Dropzone (Dashboard Inline Workflow) ──────────────────────── */

function initDropzone() {
    const zone      = document.getElementById('mriDropzone');
    const fileInput = document.getElementById('mriFileInput');
    if (!zone || !fileInput) return;

    zone.addEventListener('dragenter', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', ()  => zone.classList.remove('drag-over'));

    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length) {
            try {
                const dt = new DataTransfer();
                dt.items.add(files[0]);
                fileInput.files = dt.files;
            } catch (_) {}
            onFileSelected(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) onFileSelected(fileInput.files[0]);
    });
}

function onFileSelected(file) {
    const card   = document.getElementById('selectedFileCard');
    const nameEl = document.getElementById('selectedFileName');
    const sizeEl = document.getElementById('selectedFileSize');

    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = `${(file.size / 1048576).toFixed(2)} MB`;
    if (card)   card.style.display = 'flex';

    checkAnalyzeReady();
}

/* ─── Analyze Button Enablement & Processing State ─────────────── */

function checkAnalyzeReady() {
    const patientSelect = document.getElementById('patientSelect');
    const fileInput     = document.getElementById('mriFileInput');
    const analyzeBtn    = document.getElementById('analyzeBtn');
    if (!analyzeBtn) return;

    const hasPatient = patientSelect && patientSelect.value;
    const hasFile    = fileInput && fileInput.files.length > 0;
    analyzeBtn.disabled = !(hasPatient && hasFile);
}

function initPatientSelect() {
    const sel = document.getElementById('patientSelect');
    if (sel) sel.addEventListener('change', checkAnalyzeReady);
}

function initAnalysisFormProcessing() {
    document.querySelectorAll('form[action*="upload_mri"]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const patientInput = form.querySelector('select[name="patient_id"], input[name="patient_id"]');
            const fileInput    = form.querySelector('input[name="mri_file"]');
            const submitBtn    = form.querySelector('button[type="submit"]');

            if (!patientInput || !patientInput.value || !fileInput || !fileInput.files.length) {
                form.reportValidity?.();
                return;
            }

            // Disable submit button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.display = 'none';
            }

            // Find or create progress container
            let progressCard = form.querySelector('.mri-progress-card');
            if (!progressCard) {
                progressCard = document.createElement('div');
                progressCard.className = 'mri-progress-card';
                progressCard.innerHTML = `
                    <div class="mri-progress-header">
                        <div class="mri-progress-title-group">
                            <span class="mri-progress-status-dot" id="progressDot"></span>
                            <span class="mri-progress-title" id="progressTitle">Analyzing MRI</span>
                        </div>
                        <span class="mri-progress-percent" id="progressPercent">20%</span>
                    </div>
                    <div class="mri-progress-track">
                        <div class="mri-progress-bar" id="progressBar" style="width: 20%;"></div>
                    </div>
                    <div class="mri-progress-footer">
                        <span class="mri-progress-stage-text" id="progressStage">Preparing scan &amp; validating input...</span>
                        <span class="mri-progress-engine-badge">VMamba Engine</span>
                    </div>
                `;
                form.appendChild(progressCard);
            }

            progressCard.style.display = 'block';

            const dotEl     = progressCard.querySelector('#progressDot');
            const titleEl   = progressCard.querySelector('#progressTitle');
            const percentEl = progressCard.querySelector('#progressPercent');
            const barEl     = progressCard.querySelector('#progressBar');
            const stageEl   = progressCard.querySelector('#progressStage');

            function setStage(percent, stageText, titleText) {
                if (barEl) barEl.style.width = `${percent}%`;
                if (percentEl) percentEl.textContent = `${percent}%`;
                if (stageEl) stageEl.textContent = stageText;
                if (titleText && titleEl) titleEl.textContent = titleText;
            }

            // Stage 1: Preparing scan
            setStage(20, 'Preparing scan & validating input...', 'Analyzing MRI');

            // Stage 2 & 3 timed progression while request is in flight
            const stageTimer1 = setTimeout(() => {
                setStage(40, 'Preprocessing slice (224×224, ImageNet norm)...');
            }, 180);

            const stageTimer2 = setTimeout(() => {
                setStage(65, 'Running VMamba Visual State Space inference...');
            }, 450);

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                clearTimeout(stageTimer1);
                clearTimeout(stageTimer2);

                const data = await response.json().catch(() => null);

                if (response.ok && data && data.success) {
                    // Stage 4: Generating assessment
                    setStage(85, 'Generating clinical diagnostic assessment...');

                    // Stage 5: Finalizing report (100%)
                    setTimeout(() => {
                        setStage(100, 'VMamba assessment generated successfully', '✓ MRI Analysis Complete');
                        if (dotEl) dotEl.classList.add('complete');
                        if (barEl) barEl.classList.add('complete');
                        if (percentEl) percentEl.classList.add('complete');

                        // Smooth redirect after clinician sees verified 100% complete state
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 500);
                    }, 220);

                } else {
                    const errMsg = (data && data.error) ? data.error : 'Analysis failed. Please check the scan file and try again.';
                    if (titleEl) titleEl.textContent = '✕ Analysis Failed';
                    if (stageEl) stageEl.textContent = errMsg;
                    if (percentEl) {
                        percentEl.textContent = 'Failed';
                        percentEl.classList.add('error');
                    }
                    if (dotEl) dotEl.classList.add('error');
                    if (barEl) {
                        barEl.style.width = '100%';
                        barEl.classList.add('error');
                    }
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.style.display = 'block';
                        submitBtn.textContent = 'Retry Analysis →';
                    }
                }

            } catch (err) {
                clearTimeout(stageTimer1);
                clearTimeout(stageTimer2);

                if (titleEl) titleEl.textContent = '✕ Analysis Failed';
                if (stageEl) stageEl.textContent = 'Network or server communication error.';
                if (percentEl) {
                    percentEl.textContent = 'Error';
                    percentEl.classList.add('error');
                }
                if (dotEl) dotEl.classList.add('error');
                if (barEl) {
                    barEl.style.width = '100%';
                    barEl.classList.add('error');
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.display = 'block';
                    submitBtn.textContent = 'Retry Analysis →';
                }
            }
        });
    });
}

/* ─── Modal System ──────────────────────────────────────────────── */

function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add('active');
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove('active');
}

function openNewAnalysisModal(patientId, patientName) {
    const modal = document.getElementById('analysisModal');
    if (!modal) return;

    if (patientId) {
        const sel = modal.querySelector('select[name="patient_id"]');
        if (sel) sel.value = patientId;
    }

    modal.classList.add('active');
}

function initModals() {
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });

    document.querySelectorAll('[data-close-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
            const m = btn.closest('.modal-overlay');
            if (m) m.classList.remove('active');
        });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
        }
    });
}

/* ─── Flash Auto-Dismiss ─────────────────────────────────────────── */

function initFlashDismiss() {
    setTimeout(() => {
        document.querySelectorAll('.flash-msg').forEach(el => {
            el.style.transition = 'opacity 0.4s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 420);
        });
    }, 5500);
}

/* ─── Bootstrap ─────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initGreeting();
    initDropzone();
    initPatientSelect();
    initAnalysisFormProcessing();
    initModals();
    initFlashDismiss();
});
