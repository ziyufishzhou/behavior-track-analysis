/* 导航切换 + 共用函数 */

// 页面切换
document.querySelectorAll('#nav-list .nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.getElementById(item.dataset.page).classList.add('active');
        item.classList.add('active');
    });
});

// 通用 fetch 封装
async function api(url, options = {}) {
    const isFormData = options.body && options.body instanceof FormData;
    const headers = isFormData ? {} : { 'Content-Type': 'application/json' };
    const resp = await fetch(url, { headers, ...options });
    if (!resp.ok) {
        let detail = '';
        try {
            const data = await resp.json();
            detail = data?.error ? `：${data.error}` : '';
        } catch (_) {}
        const msg = resp.status === 409 ? '任务正在运行中，请等待完成' : `请求失败: ${resp.status}${detail}`;
        appendLog(msg + '\n', 'error');
        toast(msg, 'error');
        return null;
    }
    return resp.json();
}

// Toast 消息
function toast(msg, type = 'info') {
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText = `position:fixed;top:20px;right:20px;padding:10px 20px;border-radius:6px;z-index:9999;
        background:${type === 'error' ? 'var(--red)' : type === 'warn' ? 'var(--peach)' : 'var(--green)'};
        color:var(--mantle);font-weight:bold;font-size:13px;`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

// ====== 项目状态 ======
loadProjectStatus();
document.getElementById('status-refresh').addEventListener('click', loadProjectStatus);

function shortPath(path) {
    if (!path) return '未生成';
    const parts = path.replaceAll('\\', '/').split('/');
    return parts.length > 2 ? `${parts.at(-2)}/${parts.at(-1)}` : path;
}

function yesNo(ok) {
    return ok ? '已就绪' : '未就绪';
}

function setStatusText(id, value, ok = null) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = value;
    if (ok !== null) el.className = ok ? 'state-ok' : 'state-warn';
}

function loadProjectStatus() {
    api('/api/status').then(data => {
        if (!data) return;
        setStatusText('status-video-path', data.video.path, data.video.exists);
        setStatusText('status-video-count', `${data.video.count} 个`, data.video.count > 0);
        setStatusText('status-dlc-python', data.dlc.python || '未配置', data.dlc.python_exists);
        setStatusText('status-dlc-state', yesNo(data.dlc.python_exists), data.dlc.python_exists);
        setStatusText('status-csv-raw', `${data.csv.raw} 个`, data.csv.raw > 0);
        setStatusText('status-csv-fixed', `${data.csv.fixed} 个`, data.csv.fixed > 0);
        setStatusText('status-csv-grouped', `${data.csv.grouped} 个`, data.csv.grouped > 0);
        setStatusText('status-meta-file', yesNo(data.metadata.exists), data.metadata.exists);
        setStatusText('status-meta-rows', `${data.metadata.rows} 行`, data.metadata.rows > 0);
        setStatusText('status-roi-of', yesNo(data.roi.OF), data.roi.OF);
        setStatusText('status-roi-epm', yesNo(data.roi.EPM), data.roi.EPM);
        setStatusText('status-roi-tct', yesNo(data.roi.TCT), data.roi.TCT);
        setStatusText('status-summary-of', shortPath(data.summary.OF), Boolean(data.summary.OF));
        setStatusText('status-summary-epm', shortPath(data.summary.EPM), Boolean(data.summary.EPM));
        setStatusText('status-summary-tct', shortPath(data.summary.TCT), Boolean(data.summary.TCT));
    });
}

// ====== 导入视频 ======
let importPreview = {};  // { filename: { exp, group, cond, mouse, phase } }

loadVideoDir();
loadImportVideos();

document.getElementById('import-video-dir-save').addEventListener('click', saveVideoDir);
document.getElementById('import-refresh').addEventListener('click', loadImportVideos);
document.getElementById('import-clear').addEventListener('click', () => {
    document.querySelectorAll('#import-video-list li.selected').forEach(li => li.classList.remove('selected'));
});
document.getElementById('import-exp').addEventListener('input', e => {
    document.getElementById('import-phase-row').style.display = e.target.value.toUpperCase() === 'TCT' ? 'flex' : 'none';
});
document.getElementById('import-apply').addEventListener('click', applyImportLabels);
document.getElementById('import-save').addEventListener('click', () => {
    api('/api/import/metadata', { method: 'POST', body: JSON.stringify({ rows: getImportRows() }) }).then(r => {
        if (!r) return;
        if (r.task_id) {
            appendLog('保存元数据并分组中...\n', 'normal');
            startLogStream(r.task_id, ok => {
                toast(ok ? '元数据已保存并分组完成' : '分组出错', ok ? 'info' : 'error');
            });
        } else {
            toast(r.message || '元数据已保存');
        }
    });
});
document.getElementById('import-upload').addEventListener('click', () => {
    const input = document.getElementById('import-upload-input');
    if (!input.files.length) { toast('请先选择视频文件', 'warn'); return; }
    const fd = new FormData();
    for (const f of input.files) fd.append('videos', f);
    toast('上传中...');
    fetch('/api/import/upload', { method: 'POST', body: fd }).then(r => r.json()).then(data => {
        if (data && data.uploaded) {
            toast(`已上传 ${data.uploaded} 个视频`);
            loadImportVideos();
        } else {
            toast(data?.error || '上传失败', 'error');
        }
    });
});

function loadVideoDir() {
    api('/api/import/video-dir').then(data => {
        if (!data) return;
        document.getElementById('import-video-dir').value = data.video_dir || '';
        updateVideoDirStatus(data);
    });
}

function saveVideoDir() {
    const video_dir = document.getElementById('import-video-dir').value.trim();
    if (!video_dir) { toast('请输入视频根目录', 'warn'); return; }
    api('/api/import/video-dir', { method: 'POST', body: JSON.stringify({ video_dir }) }).then(data => {
        if (!data) return;
        updateVideoDirStatus(data);
        toast('视频根目录已保存');
        loadImportVideos();
        loadDlcVideos();
    });
}

function updateVideoDirStatus(data) {
    const status = document.getElementById('import-video-dir-status');
    if (!status) return;
    const text = data.exists ? `当前视频根目录：${data.video_dir}` : `目录不存在：${data.video_dir}`;
    status.textContent = text;
    status.style.color = data.exists ? 'var(--subtext0)' : 'var(--red)';
}

function loadImportVideos() {
    appendLog('正在加载视频列表...\n', 'normal');
    api('/api/import/videos').then(data => {
        if (!data) { appendLog('加载视频列表失败\n', 'error'); return; }
        updateVideoDirStatus(data);
        const ul = document.getElementById('import-video-list');
        ul.innerHTML = '';
        if (!data.videos.length) {
            ul.innerHTML = '<li style="color:var(--overlay0)">当前视频目录下没有视频文件</li>';
            appendLog(`视频目录为空：${data.video_dir}\n`, 'warn');
            return;
        }
        data.videos.forEach(name => {
            const li = document.createElement('li');
            li.textContent = name;
            li.title = name;
            li.addEventListener('click', e => {
                if (e.ctrlKey || e.metaKey) {
                    li.classList.toggle('selected');
                } else {
                    ul.querySelectorAll('li').forEach(l => l.classList.remove('selected'));
                    li.classList.add('selected');
                }
            });
            ul.appendChild(li);
        });
        appendLog(`从 ${data.video_dir} 加载了 ${data.videos.length} 个视频\n`, 'normal');
    });
    // 加载已有元数据到预览表
    api('/api/import/metadata').then(data => {
        if (!data || !data.columns.length) { appendLog('无元数据\n', 'normal'); return; }
        importPreview = {};
        const cols = data.columns;
        data.rows.forEach(row => {
            const name = row[0] || '';
            importPreview[name] = {
                exp: row[1] || '', group: row[2] || '', cond: row[3] || '',
                mouse: row[4] || '', phase: row[5] || ''
            };
        });
        renderImportPreview();
        appendLog(`加载了 ${data.rows.length} 条元数据\n`, 'normal');
    });
}

function applyImportLabels() {
    const exp = document.getElementById('import-exp').value.trim();
    const group = document.getElementById('import-group').value.trim();
    const cond = document.getElementById('import-cond').value.trim();
    const mouse = document.getElementById('import-mouse').value.trim();
    const phase = exp.toUpperCase() === 'TCT' ? document.getElementById('import-phase').value : '';
    const selected = document.querySelectorAll('#import-video-list li.selected');
    if (!selected.length) { toast('请先选中视频', 'warn'); return; }
    selected.forEach(li => {
        const name = li.textContent;
        importPreview[name] = { exp, group, cond, mouse: mouse || name, phase };
    });
    renderImportPreview();
    toast(`已应用标签到 ${selected.length} 个视频`);
}

function getImportRows() {
    return Object.entries(importPreview).map(([name, t]) => ({
        FileName: name, Experiment: t.exp, Group: t.group,
        Condition: t.cond, MouseID: t.mouse, Phase: t.phase
    }));
}

function renderImportPreview() {
    const tbody = document.querySelector('#import-preview tbody');
    tbody.innerHTML = '';
    for (const [name, t] of Object.entries(importPreview)) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${name}</td><td>${t.exp}</td><td>${t.group}</td><td>${t.cond}</td><td>${t.mouse}</td><td>${t.phase}</td>`;
        tbody.appendChild(tr);
    }
}

// ====== DLC 分析 ======
// 页面加载时自动填充
api('/api/dlc/models').then(data => { if (data && data.models.length) document.getElementById('dlc-model').value = data.models[0]; });
loadDlcPython();
loadDlcVideos();
document.getElementById('dlc-model-browse').addEventListener('click', () => {
    api('/api/dlc/models').then(data => { if (data && data.models.length) document.getElementById('dlc-model').value = data.models[0]; });
});
document.getElementById('dlc-python-save').addEventListener('click', saveDlcPython);

function loadDlcPython() {
    api('/api/dlc/python').then(data => {
        if (!data) return;
        document.getElementById('dlc-python').value = data.python || '';
        updateDlcPythonStatus(data);
    });
}

function saveDlcPython() {
    const python = document.getElementById('dlc-python').value.trim();
    if (!python) { toast('请输入 DLC Python 路径', 'warn'); return; }
    api('/api/dlc/python', { method: 'POST', body: JSON.stringify({ python }) }).then(data => {
        if (!data) return;
        updateDlcPythonStatus(data);
        toast('DLC Python 路径已保存');
    });
}

function updateDlcPythonStatus(data) {
    const status = document.getElementById('dlc-python-status');
    if (!status) return;
    if (data.exists) {
        status.textContent = `当前 DLC Python：${data.python}`;
        status.style.color = 'var(--subtext0)';
    } else if (data.python) {
        status.textContent = `DLC Python 不存在：${data.python}`;
        status.style.color = 'var(--red)';
    } else {
        status.textContent = '用于运行 DeepLabCut。未配置时不能执行 DLC 分析。';
        status.style.color = 'var(--red)';
    }
}

function loadDlcVideos() {
    api('/api/dlc/videos').then(data => {
        if (!data) return;
        const dirStatus = document.getElementById('dlc-video-dir-status');
        if (dirStatus) dirStatus.textContent = `点击视频可选中（高亮），不选中则分析全部。当前视频根目录：${data.video_dir}`;
        const ul = document.getElementById('dlc-video-list');
        ul.innerHTML = '';
        if (data.videos.length === 0) {
            ul.innerHTML = '<li style="color:var(--overlay0)">当前视频目录下没有视频文件</li>';
            document.getElementById('dlc-video-count').textContent = '0 个视频';
            return;
        }
        data.videos.forEach(v => {
            const li = document.createElement('li');
            li.textContent = v;
            li.addEventListener('click', () => li.classList.toggle('selected'));
            ul.appendChild(li);
        });
        document.getElementById('dlc-video-count').textContent = `${data.videos.length} 个视频`;
    });
}
document.getElementById('dlc-refresh').addEventListener('click', loadDlcVideos);
document.getElementById('dlc-run').addEventListener('click', () => {
    const model = document.getElementById('dlc-model').value.trim();
    const shuffle = document.getElementById('dlc-shuffle').value;
    if (!model) { toast('请输入或选择模型路径', 'warn'); return; }
    // 收集选中的视频（如果没有选中则分析全部）
    const selectedLis = document.querySelectorAll('#dlc-video-list li.selected');
    const video_names = selectedLis.length ? Array.from(selectedLis).map(li => li.textContent) : [];
    api('/api/dlc/run', { method: 'POST', body: JSON.stringify({ model_path: model, shuffle: parseInt(shuffle), video_names }) }).then(r => r && startLogStream(r.task_id));
});

// ====== 预处理 ======
['collect', 'fix', 'group', 'meta'].forEach(step => {
    document.getElementById(`preprocess-${step}-run`).addEventListener('click', () => {
        const update = document.getElementById('preprocess-update').checked;
        api(`/api/preprocess/${step === 'meta' ? 'metadata' : step}`, { method: 'POST', body: JSON.stringify({ update }) }).then(r => {
            if (!r) return;
            setStatus(`preprocess-${step}-status`, 'running');
            startLogStream(r.task_id, () => setStatus(`preprocess-${step}-status`, 'done'));
        });
    });
});
document.getElementById('preprocess-all').addEventListener('click', () => {
    const update = document.getElementById('preprocess-update').checked;
    api('/api/preprocess/all', { method: 'POST', body: JSON.stringify({ update }) }).then(r => {
        if (!r) return;
        ['collect', 'fix', 'group', 'meta'].forEach(s => setStatus(`preprocess-${s}-status`, 'running'));
        startLogStream(r.task_id, () => ['collect', 'fix', 'group', 'meta'].forEach(s => setStatus(`preprocess-${s}-status`, 'done')));
    });
});

// ====== ROI 标注 ======
['of', 'epm', 'tct'].forEach(exp => {
    document.getElementById(`roi-${exp}-launch`).addEventListener('click', () => {
        api(`/api/roi/launch/${exp}`, { method: 'POST' }).then(r => r && toast('ROI 工具已启动'));
    });
});

// ====== 数据分析 ======
api('/api/analyze/config').then(data => {
    if (!data) return;
    document.getElementById('analyze-fps').value = data.FPS;
    document.getElementById('analyze-like').value = data.LIKELIHOOD_THRESHOLD;
    document.getElementById('analyze-of-time').value = data.OF_ANALYSIS_MINUTES;
    document.getElementById('analyze-epm-time').value = data.EPM_ANALYSIS_MINUTES;
    document.getElementById('analyze-tct-time').value = data.TCT_ANALYSIS_MINUTES;
});
api('/api/analyze/roi-status').then(data => {
    if (!data) return;
    ['of', 'epm', 'tct'].forEach(exp => {
        setRoiBadge(`analyze-${exp}-roi`, data[exp]);
        setRoiBadge(`roi-${exp}-status`, data[exp]);
    });
});
document.getElementById('analyze-run').addEventListener('click', () => {
    setStatus('analyze-status', 'running');
    const body = {
        of: document.getElementById('analyze-of').checked,
        epm: document.getElementById('analyze-epm').checked,
        tct: document.getElementById('analyze-tct').checked,
        fps: parseInt(document.getElementById('analyze-fps').value),
        likelihood: parseFloat(document.getElementById('analyze-like').value),
        of_time: parseInt(document.getElementById('analyze-of-time').value),
        epm_time: parseInt(document.getElementById('analyze-epm-time').value),
        tct_time: parseInt(document.getElementById('analyze-tct-time').value),
    };
    api('/api/analyze/run', { method: 'POST', body: JSON.stringify(body) }).then(r => {
        if (!r) { setStatus('analyze-status', 'error'); return; }
        startLogStream(r.task_id, ok => setStatus('analyze-status', ok ? 'done' : 'error'));
    });
});

// ====== 绘图设置 (Prism Style) ======
// 加载配色方案
api('/api/plot/palettes').then(data => {
  if (!data) return;
  const sel = document.getElementById('plot-palette');
  sel.innerHTML = '<option value="">自定义</option>';
  data.palettes.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.name; opt.textContent = p.display_name;
    sel.appendChild(opt);
  });
  // 默认选中第一个预设
  if (data.palettes.length) {
    sel.value = data.palettes[0].name;
    applyPaletteColors(data.palettes[0]);
  }
  // 切换配色方案时同步颜色选择器
  sel.addEventListener('change', () => {
    const found = data.palettes.find(p => p.name === sel.value);
    if (found) applyPaletteColors(found);
  });
});

function applyPaletteColors(pal) {
  if (pal.colors && pal.colors[0]) document.getElementById('plot-color-0').value = pal.colors[0];
  if (pal.colors && pal.colors[1]) document.getElementById('plot-color-1').value = pal.colors[1];
  if (pal.scatter) document.getElementById('plot-color-scatter').value = pal.scatter;
  if (pal.connect) document.getElementById('plot-color-connect').value = pal.connect;
  if (pal.edge) document.getElementById('plot-color-edge').value = pal.edge;
}

// 手动改颜色 → 切换到"自定义"
['plot-color-0','plot-color-1','plot-color-scatter','plot-color-connect','plot-color-edge'].forEach(id => {
  document.getElementById(id).addEventListener('input', () => {
    document.getElementById('plot-palette').value = '';
  });
});

document.getElementById('plot-exp').addEventListener('change', () => autoFindPlot());
document.getElementById('plot-auto-find').addEventListener('click', () => autoFindPlot());
document.getElementById('plot-generate').addEventListener('click', () => {
  setStatus('plot-status', 'running');
  const body = {
    experiment: document.getElementById('plot-exp').value,
    source: document.getElementById('plot-source').value,
    chart_type: document.getElementById('plot-chart-type').value,
    palette_name: document.getElementById('plot-palette').value,
    force_test: document.getElementById('plot-force-test').value,
    title: document.getElementById('plot-title').value,
    bar_width: parseFloat(document.getElementById('plot-bar-width').value),
    bar_gap: parseFloat(document.getElementById('plot-bar-gap').value),
    point_size: parseInt(document.getElementById('plot-point-size').value),
    errorbar: document.getElementById('plot-errorbar').value,
    alpha: parseFloat(document.getElementById('plot-alpha').value),
    fill_alpha: parseFloat(document.getElementById('plot-fill-alpha').value),
    edge_width: parseFloat(document.getElementById('plot-edge-width').value),
    figure_width_mm: parseFloat(document.getElementById('plot-fig-width').value),
    color_0: document.getElementById('plot-color-0').value,
    color_1: document.getElementById('plot-color-1').value,
    color_scatter: document.getElementById('plot-color-scatter').value,
    color_connect: document.getElementById('plot-color-connect').value,
    color_edge: document.getElementById('plot-color-edge').value,
    pdf: document.getElementById('plot-pdf').checked,
    png: document.getElementById('plot-png').checked,
    dpi: parseInt(document.getElementById('plot-dpi').value),
  };
  api('/api/plot/generate', { method: 'POST', body: JSON.stringify(body) }).then(r => {
    if (!r) { setStatus('plot-status', 'error'); return; }
    startLogStream(r.task_id, ok => {
      setStatus('plot-status', ok ? 'done' : 'error');
      if (ok) {
        loadPlotPreview();
        loadPlotStats();
      }
    });
  });
});
document.getElementById('plot-open-dir').addEventListener('click', loadPlotPreview);

// AI 生成
document.getElementById('plot-ai-run').addEventListener('click', () => {
  const fileInput = document.getElementById('plot-ai-image');
  if (!fileInput.files.length) { toast('请先选择示例图片', 'warn'); return; }
  const fd = new FormData();
  fd.append('image', fileInput.files[0]);
  fd.append('source', document.getElementById('plot-source').value);
  fd.append('experiment', document.getElementById('plot-exp').value);
  setStatus('plot-status', 'running');
  fetch('/api/plot/ai-generate', { method: 'POST', body: fd }).then(r => r.json()).then(r => {
    if (!r || r.error) { toast(r?.error || 'AI 生成失败', 'error'); setStatus('plot-status', 'error'); return; }
    startLogStream(r.task_id, ok => {
      setStatus('plot-status', ok ? 'done' : 'error');
      if (ok) loadPlotPreview();
    });
  });
});

function autoFindPlot() {
  const exp = document.getElementById('plot-exp').value;
  api(`/api/plot/auto-find/${exp}`).then(data => {
    if (!data) return;
    document.getElementById('plot-source').value = data.path || '';
    if (data.path) {
      appendLog(`找到绘图数据：${data.path}\n`, 'normal');
    } else {
      appendLog(`未找到 ${exp} 的 summary Excel，请手动填写数据文件路径\n`, 'warn');
    }
  });
}

function loadPlotPreview() {
  const exp = document.getElementById('plot-exp').value.toLowerCase();
  api(`/api/plot/figures/${exp}`).then(data => {
    if (!data || !data.figures.length) { toast('没有找到图表文件', 'warn'); return; }
    const area = document.getElementById('plot-preview-area');
    // 优先找 PNG，否则展示 PDF 链接
    const pngs = data.figures.filter(f => f.endsWith('.png'));
    const pdfs = data.figures.filter(f => f.endsWith('.pdf'));
    let html = '';
    if (pngs.length) {
      html = `<img src="/api/plot/figure/${exp}/${encodeURIComponent(pngs[0])}" style="max-height:400px;max-width:100%">`;
    } else if (pdfs.length) {
      html = `<a href="/api/plot/figure/${exp}/${encodeURIComponent(pdfs[0])}" target="_blank" style="color:var(--blue)">${pdfs[0]}</a>`;
    }
    // 文件列表
    html += '<div style="margin-top:8px;font-size:11px;color:var(--subtext0)">';
    data.figures.slice(0, 10).forEach(f => {
      const isImg = f.endsWith('.png');
      html += `<div><a href="/api/plot/figure/${exp}/${encodeURIComponent(f)}" ${isImg ? 'target="_blank"' : 'download'} style="color:var(--blue)">${f}</a></div>`;
    });
    html += '</div>';
    area.innerHTML = html;
  });
}

function loadPlotStats() {
  const exp = document.getElementById('plot-exp').value.toLowerCase();
  api(`/api/plot/stats/${exp}`).then(data => {
    if (!data || !data.stats || !data.stats.length) return;
    const tbody = document.querySelector('#plot-stats-table tbody');
    tbody.innerHTML = '';
    data.stats.forEach(s => {
      const tr = document.createElement('tr');
      const eff = s.effect_size != null ? `${s.effect_name || ''}=${s.effect_size}` : '';
      tr.innerHTML = `<td>${s.group || ''}</td><td>${s.metric || ''}</td><td>${s.test || ''}</td>
        <td>${s.p != null ? s.p.toFixed(4) : ''}</td><td>${s.star || ''}</td><td>${eff}</td>`;
      tbody.appendChild(tr);
    });
  });
}

// ====== 元数据编辑 ======
loadMetadata();
document.getElementById('meta-rescan').addEventListener('click', () => {
    const update = document.getElementById('meta-update').checked;
    api('/api/metadata/rescan', { method: 'POST', body: JSON.stringify({ update }) }).then(data => {
        if (!data) return;
        renderMetaTable(data.columns || [], data.rows || []);
        toast('重新扫描完成');
    });
});
document.getElementById('meta-save').addEventListener('click', () => {
    const data = readMetaTable();
    const update = document.getElementById('meta-update').checked;
    api('/api/metadata', { method: 'POST', body: JSON.stringify({ ...data, update }) }).then(r => r && toast('元数据已保存'));
});
document.getElementById('meta-add-col').addEventListener('click', () => {
    const name = document.getElementById('meta-new-col').value.trim();
    if (!name) return;
    api('/api/metadata/columns', { method: 'POST', body: JSON.stringify({ name }) }).then(() => { document.getElementById('meta-new-col').value = ''; loadMetadata(); });
});

function loadMetadata() {
    api('/api/metadata').then(data => {
        if (!data) return;
        renderMetaTable(data.columns, data.rows);
    });
}

function renderMetaTable(columns, rows) {
    const thead = document.querySelector('#meta-table thead');
    const tbody = document.querySelector('#meta-table tbody');
    thead.innerHTML = '<tr>' + columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
    tbody.innerHTML = rows.map(row => '<tr>' + row.map(v => `<td contenteditable="true">${v ?? ''}</td>`).join('') + '</tr>').join('');
}

function readMetaTable() {
    const thead = document.querySelector('#meta-table thead');
    const tbody = document.querySelector('#meta-table tbody');
    const columns = Array.from(thead.querySelectorAll('th')).map(th => th.textContent);
    const rows = Array.from(tbody.querySelectorAll('tr')).map(tr =>
        Array.from(tr.querySelectorAll('td')).map(td => td.textContent)
    );
    return { columns, rows };
}

// ====== 工具函数 ======
function setStatus(id, state) {
    const el = id && document.getElementById(id);
    const map = { running: ['运行中...', 'var(--blue)'], done: ['完成', 'var(--green)'], error: ['出错', 'var(--red)'] };
    const [text, color] = map[state] || ['就绪', 'var(--overlay0)'];
    if (el) { el.textContent = text; el.style.color = color; }
}

function setRoiBadge(id, configured) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = configured ? '已配置' : '未配置';
    el.style.color = configured ? 'var(--green)' : 'var(--red)';
}

function appendLog(text, type) {
    const el = document.getElementById('log-console');
    const span = document.createElement('span');
    span.className = `log-${type || 'normal'}`;
    span.textContent = text;
    el.appendChild(span);
    el.scrollTop = el.scrollHeight;
}

// 日志面板折叠
document.getElementById('log-toggle').addEventListener('click', () => {
    document.getElementById('log-panel').classList.toggle('collapsed');
});
document.getElementById('log-clear').addEventListener('click', () => {
    document.getElementById('log-console').innerHTML = '';
    updateProgressBar(null);
});
