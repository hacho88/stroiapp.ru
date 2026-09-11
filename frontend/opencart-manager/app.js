const { useState, useEffect, useCallback } = React;

const API_URL = 'https://stroiapp.ru/index.php?route=api/ai_manager';
const TOKEN = 'change_this_ai_manager_token';

function api(action, params = {}) {
    const query = new URLSearchParams({ action, token: TOKEN, ...params });
    return fetch(`${API_URL}&${query}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    }).then(r => r.json());
}

function apiPost(action, body) {
    return fetch(`${API_URL}&action=${action}&token=${TOKEN}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }).then(r => r.json());
}

function FileIcon({ name }) {
    const ext = name.split('.').pop().toLowerCase();
    const icons = { twig: '&#x1F4C4;', css: '&#x1F3A8;', js: '&#x26A1;', php: '&#x1F4DD;', json: '&#x1F4C1;', xml: '&#x1F4C3;', html: '&#x1F310;', txt: '&#x1F4D6;' };
    return <span className="ficon" dangerouslySetInnerHTML={{ __html: icons[ext] || '&#x1F4C4;' }} />;
}

function App() {
    const [tab, setTab] = useState('files');
    const [files, setFiles] = useState([]);
    const [currentFile, setCurrentFile] = useState(null);
    const [content, setContent] = useState('');
    const [original, setOriginal] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [previewUrl, setPreviewUrl] = useState('https://stroiapp.ru');
    const [showPreview, setShowPreview] = useState(false);

    useEffect(() => {
        loadFiles();
    }, []);

    const loadFiles = async () => {
        setLoading(true);
        try {
            const data = await api('theme/list', { type: 'all' });
            if (data.status === 'ok') {
                setFiles(data.items || []);
            }
        } catch (e) {
            setMessage('Ошибка загрузки файлов: ' + e.message);
        }
        setLoading(false);
    };

    const openFile = async (path) => {
        setLoading(true);
        try {
            const data = await api('theme/read', { path });
            if (data.status === 'ok') {
                setCurrentFile(data);
                setContent(data.content);
                setOriginal(data.content);
                setShowPreview(path.endsWith('.twig') || path.endsWith('.css'));
            } else {
                setMessage(data.error || 'Ошибка чтения файла');
            }
        } catch (e) {
            setMessage('Ошибка: ' + e.message);
        }
        setLoading(false);
    };

    const saveFile = async () => {
        if (!currentFile) return;
        setLoading(true);
        try {
            const data = await apiPost('theme/write', { path: currentFile.path, content });
            if (data.status === 'written') {
                setOriginal(content);
                setMessage('Сохранено!');
                setTimeout(() => setMessage(''), 2000);
            } else {
                setMessage(data.error || 'Ошибка сохранения');
            }
        } catch (e) {
            setMessage('Ошибка сохранения: ' + e.message);
        }
        setLoading(false);
    };

    const clearCache = async () => {
        setLoading(true);
        try {
            const data = await apiPost('site/clearCache', {});
            setMessage(`Кэш очищен (${data.deleted || 0} файлов)`);
            setTimeout(() => setMessage(''), 3000);
        } catch (e) {
            setMessage('Ошибка очистки кэша');
        }
        setLoading(false);
    };

    const grouped = files.reduce((acc, f) => {
        const type = f.path.split('/')[0];
        if (!acc[type]) acc[type] = [];
        acc[type].push(f);
        return acc;
    }, {});

    const isDirty = content !== original;

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h1>StroiApp Manager</h1>
                    <p>OpenCart Theme Control</p>
                </div>
                <nav className="nav">
                    <button className={tab === 'files' ? 'active' : ''} onClick={() => setTab('files')}>
                        <span className="icon">&#x1F4C1;</span> Файлы темы
                    </button>
                    <button className={tab === 'designer' ? 'active' : ''} onClick={() => setTab('designer')}>
                        <span className="icon">&#x1F3A8;</span> Конструктор
                    </button>
                    <button className={tab === 'settings' ? 'active' : ''} onClick={() => setTab('settings')}>
                        <span className="icon">&#x2699;&#xFE0F;</span> Настройки
                    </button>
                    <button onClick={() => window.open('https://stroiapp.ru', '_blank')}>
                        <span className="icon">&#x1F310;</span> Открыть сайт
                    </button>
                </nav>
            </aside>

            <main className="main">
                <div className="toolbar">
                    <h2>{currentFile ? currentFile.path : 'Выберите файл'}</h2>
                    {currentFile && (
                        <>
                            <button className="btn btn-primary" onClick={saveFile} disabled={!isDirty || loading}>
                                &#x1F4BE; {loading ? 'Сохранение...' : 'Сохранить'}
                            </button>
                            <button className="btn btn-secondary" onClick={() => setContent(original)} disabled={!isDirty}>
                                &#x21A9; Отменить
                            </button>
                            <button className="btn btn-success" onClick={clearCache} disabled={loading}>
                                &#x1F504; Очистить кэш
                            </button>
                            <button className="btn btn-secondary" onClick={() => setShowPreview(!showPreview)}>
                                {showPreview ? '&#x1F441; Скрыть' : '&#x1F441; Превью'}
                            </button>
                        </>
                    )}
                </div>

                {message && <div className="error-box">{message}</div>}

                {tab === 'files' && (
                    <div className="workspace">
                        <div className="file-tree">
                            <h3>&#x1F4C1; Файлы темы UniShop2</h3>
                            {loading && <div className="loading">Загрузка...</div>}
                            {Object.keys(grouped).sort().map(type => (
                                <div className="folder-group" key={type}>
                                    <div className="folder-label">{type}</div>
                                    {grouped[type].map(f => (
                                        <div
                                            key={f.path}
                                            className={`tree-item ${currentFile?.path === f.path ? 'active' : ''}`}
                                            onClick={() => openFile(f.path)}
                                        >
                                            <FileIcon name={f.name} />
                                            <span>{f.name}</span>
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>

                        {currentFile ? (
                            <div className="editor-wrap">
                                <div className="editor-tabs">
                                    <div className="editor-tab active">&#x1F4DD; Редактор</div>
                                    {isDirty && <div className="editor-tab" style={{color:'#FF4F00'}}>&#x25CF; Изменено</div>}
                                </div>
                                <div className="editor-body">
                                    <textarea
                                        className="code-editor"
                                        value={content}
                                        onChange={e => setContent(e.target.value)}
                                        spellCheck={false}
                                    />
                                    {showPreview && (
                                        <div className="preview-pane">
                                            <div className="preview-header">
                                                <span>&#x1F441; Превью сайта</span>
                                                <button className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'12px'}} onClick={() => setPreviewUrl('https://stroiapp.ru?' + Date.now())}>&#x1F504; Обновить</button>
                                            </div>
                                            <iframe className="preview-frame" src={previewUrl} />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="empty-state">
                                <span style={{fontSize:'48px'}}>&#x1F4C1;</span>
                                <p>Выберите файл из списка слева для редактирования</p>
                            </div>
                        )}
                    </div>
                )}

                {tab === 'designer' && (
                    <div className="workspace" style={{ padding: 0 }}>
                        <Designer />
                    </div>
                )}

                {tab === 'settings' && (
                    <div className="workspace" style={{padding:'40px'}}>
                        <h2 style={{marginBottom:'20px'}}>&#x2699;&#xFE0F; Настройки темы</h2>
                        <p style={{color:'#666',lineHeight:1.6,maxWidth:'600px'}}>
                            Здесь вы можете управлять глобальными настройками магазина.
                            Для изменения настроек используйте API методы <code>setting/list</code> и <code>setting/update</code>.
                        </p>
                        <div style={{marginTop:'30px',display:'flex',gap:'10px'}}>
                            <button className="btn btn-primary" onClick={clearCache}>&#x1F504; Очистить кэш OpenCart</button>
                            <button className="btn btn-secondary" onClick={() => window.open('https://stroiapp.ru/admin', '_blank')}>&#x1F510; Админ-панель</button>
                        </div>
                    </div>
                )}

                <div className="status-bar">
                    <span className={loading ? 'err' : 'ok'}>{loading ? '&#x23F3; Загрузка...' : '&#x2705; Готов'}</span>
                    <span>{files.length} файлов в теме</span>
                    {currentFile && <span>{content.length} символов | {content.split('\n').length} строк</span>}
                </div>
            </main>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
