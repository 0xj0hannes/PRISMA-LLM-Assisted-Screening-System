document.addEventListener('DOMContentLoaded', () => {
    // Tab Navigation
    const navLinks = document.querySelectorAll('.nav-links li');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(l => l.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            link.classList.add('active');
            const tabId = link.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Trigger specific actions when tabs open
            if(tabId === 'screen') updateScreenStats();
            if(tabId === 'review') loadReviews();
        });
    });

    // Ingestion Logic
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('bib-upload');
    const uploadStatus = document.getElementById('upload-status');

    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if(e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if(e.target.files.length) {
            handleFileUpload(e.target.files);
        }
    });

    async function handleFileUpload(fileList) {
        uploadStatus.innerHTML = `Uploading and processing files...`;
        const formData = new FormData();
        
        let fileCount = 0;
        for (let i = 0; i < fileList.length; i++) {
            if(fileList[i].name.endsWith('.bib')) {
                formData.append("files", fileList[i]);
                fileCount++;
            }
        }
        
        if (fileCount === 0) {
            uploadStatus.innerHTML = `<span class="error">Error: Please upload .bib files.</span>`;
            return;
        }

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if(res.ok) {
                uploadStatus.innerHTML = `<span class="success">Success! Loaded ${data.uploaded} records (Total Unique Database size: ${data.total_unique_db}).</span>`;
            } else {
                uploadStatus.innerHTML = `<span class="error">Error: ${data.error}</span>`;
            }
        } catch (err) {
            uploadStatus.innerHTML = `<span class="error">Network error.</span>`;
        }
    }

    // Screening Logic
    const btnStartScreen = document.getElementById('btn-start-screen');
    const screenProgress = document.getElementById('screen-progress');
    const progressText = document.getElementById('progress-text');
    const statTotal = document.getElementById('stat-total');
    const statScreened = document.getElementById('stat-screened');
    let screenInterval;

    async function updateScreenStats() {
        const res = await fetch('/api/screen/status');
        const data = await res.json();
        statTotal.textContent = data.total;
        statScreened.textContent = data.screened;

        if (data.is_running) {
            btnStartScreen.disabled = true;
            screenProgress.classList.remove('hidden');
            const pct = data.total > 0 ? Math.round((data.screened / data.total) * 100) : 0;
            document.getElementById('progress-fill').style.width = pct + '%';
            progressText.textContent = `Screening in progress... ${data.screened}/${data.total} (${pct}%)`;
            
            if (!screenInterval) {
                screenInterval = setInterval(updateScreenStats, 3000);
            }
        } else {
            btnStartScreen.disabled = false;
            screenProgress.classList.add('hidden');
            if (screenInterval) {
                clearInterval(screenInterval);
                screenInterval = null;
            }
        }
    }

    btnStartScreen.addEventListener('click', async () => {
        btnStartScreen.disabled = true;
        screenProgress.classList.remove('hidden');
        progressText.textContent = "Starting AI Engine...";

        const res = await fetch('/api/screen/start', { method: 'POST' });
        if(res.ok) {
            if (!screenInterval) screenInterval = setInterval(updateScreenStats, 3000);
        } else {
            btnStartScreen.disabled = false;
            progressText.textContent = "Failed to start screening.";
        }
    });

    const btnStopScreen = document.getElementById('btn-stop-screen');
    if (btnStopScreen) {
        btnStopScreen.addEventListener('click', async () => {
            await fetch('/api/screen/stop', { method: 'POST' });
            clearInterval(screenInterval);
            screenProgress.classList.add('hidden');
            btnStartScreen.disabled = false;
        });
    }

    // Review Logic
    const reviewArea = document.getElementById('review-area');
    const reviewTemplate = document.getElementById('review-template');

    let activeCriteria = {};

    async function loadCriteria() {
        try {
            const res = await fetch('/api/criteria');
            activeCriteria = await res.json();
            
            const listEl = document.getElementById('active-criteria-list');
            if (listEl) {
                listEl.innerHTML = '';
                for (const [key, c] of Object.entries(activeCriteria)) {
                    const li = document.createElement('li');
                    li.style.marginTop = '8px';
                    li.innerHTML = `<strong style="color: var(--accent-blue);">${key} (${c.name}):</strong> ${c.definition}`;
                    listEl.appendChild(li);
                }
            }
        } catch(e) {
            console.error("Failed to load criteria:", e);
        }
    }

    async function loadReviews() {
        reviewArea.innerHTML = '<div class="glass no-records-msg"><p>Loading records for review...</p></div>';
        
        try {
            const res = await fetch('/api/review');
            const data = await res.json();
            
            if(!data.reviews || data.reviews.length === 0) {
                reviewArea.innerHTML = '<div class="glass no-records-msg"><p>All matching records have already been reviewed! 🎉</p></div>';
                return;
            }

            reviewArea.innerHTML = '';
            data.reviews.forEach(item => {
                const clone = reviewTemplate.content.cloneNode(true);
                const card = clone.querySelector('.review-card');
                
                clone.querySelector('.record-id').textContent += item.record.id;
                clone.querySelector('.record-title').textContent = item.record.title;
                clone.querySelector('.record-abstract').textContent = item.record.abstract;
                
                // Dynamically build rationale
                const rationaleContainer = clone.getElementById('llm-rationale-container');
                if (rationaleContainer) {
                    rationaleContainer.removeAttribute('id'); // prevent duplicates
                    const critResults = item.result.criteria || {};
                    for (const key of Object.keys(activeCriteria)) {
                        const critData = critResults[key] || {};
                        const score = critData.score !== undefined ? parseFloat(critData.score).toFixed(2) : 'N/A';
                        const rationale = critData.rationale || '-';
                        
                        const d = document.createElement('div');
                        d.style.marginBottom = '12px';
                        d.innerHTML = `<strong>${key} Rationale (Score: <span style="color:var(--accent-blue);">${score}</span>):</strong> <span>${rationale}</span>`;
                        rationaleContainer.appendChild(d);
                    }
                }

                const btnInclude = clone.querySelector('.btn-include');
                const btnExcludeInit = clone.querySelector('.btn-exclude-init');
                const reviewActions = clone.querySelector('.review-actions');
                const excludeOptions = clone.querySelector('.exclude-options');

                btnInclude.addEventListener('click', () => submitReview(item.record.id, 'Include', 'None', card));
                btnExcludeInit.addEventListener('click', () => {
                    reviewActions.classList.add('hidden');
                    excludeOptions.classList.remove('hidden');
                });
                
                // Dynamically build exclusion buttons
                const exclusionContainer = clone.getElementById('exclude-reasons-container');
                if (exclusionContainer) {
                    exclusionContainer.removeAttribute('id'); // prevent duplicates
                    
                    const keys = Object.keys(activeCriteria);
                    // Add individual keys
                    for (const k of keys) {
                        const btn = document.createElement('button');
                        btn.className = 'btn-outline btn-ex';
                        btn.textContent = k;
                        btn.addEventListener('click', () => submitReview(item.record.id, 'Exclude', k, card));
                        exclusionContainer.appendChild(btn);
                    }
                    
                    // Add a "Multiple/Other" button
                    const btnMultiple = document.createElement('button');
                    btnMultiple.className = 'btn-outline btn-ex';
                    btnMultiple.textContent = keys.join('+');
                    btnMultiple.addEventListener('click', () => submitReview(item.record.id, 'Exclude', keys.join('+'), card));
                    exclusionContainer.appendChild(btnMultiple);
                }

                reviewArea.appendChild(clone);
            });
        } catch (e) {
            reviewArea.innerHTML = '<div class="glass no-records-msg"><p>Failed to load reviews.</p></div>';
        }
    }

    async function submitReview(recordId, decision, unmet, cardElement) {
        try {
            const res = await fetch(`/api/review/${encodeURIComponent(recordId)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision, unmet_criteria: unmet })
            });

            if(res.ok) {
                cardElement.style.opacity = '0';
                setTimeout(() => cardElement.remove(), 300);
            }
        } catch(e) {
            alert('Failed to save review');
        }
    }

    // Report Logic
    document.getElementById('btn-download-report').addEventListener('click', () => {
        window.location.href = '/api/report';
    });

    // Initial Load
    loadCriteria().then(() => {
        updateScreenStats();
    });
});
