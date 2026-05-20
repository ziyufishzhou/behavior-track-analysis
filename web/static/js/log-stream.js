/* SSE 日志流客户端 */
let currentEventSource = null;

function updateProgressBar(progress) {
    const wrap = document.getElementById('progress-bar-wrap');
    const bar = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    if (!progress) {
        wrap.classList.remove('active');
        bar.style.width = '0%';
        text.textContent = '';
        return;
    }
    wrap.classList.add('active');
    bar.style.width = progress.percent + '%';
    text.textContent = `${progress.current}/${progress.total} (${progress.percent}%) ${progress.message || ''}`;
}

function startLogStream(taskId, onDone) {
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }

    const es = new EventSource(`/api/tasks/${taskId}/stream`);
    currentEventSource = es;

    es.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.done) {
            es.close();
            currentEventSource = null;
            if (data.progress && data.progress.percent >= 100) {
                updateProgressBar(null);
            }
            if (onDone) onDone(data.success);
            return;
        }
        const text = data.text || '';
        // Update progress bar if progress data is present
        if (data.progress) {
            updateProgressBar(data.progress);
        }
        // Don't show [PROGRESS] lines in the log console
        if (text.includes('[PROGRESS]')) return;
        let type = 'normal';
        if (text.includes('[ERROR]') || text.includes('Error') || text.includes('Traceback')) type = 'error';
        else if (text.includes('[WARN') || text.includes('Warning')) type = 'warn';
        appendLog(text, type);
    };

    es.onerror = function() {
        es.close();
        currentEventSource = null;
        updateProgressBar(null);
        if (onDone) onDone(false);
    };
}