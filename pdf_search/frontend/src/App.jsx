import { useState, useEffect } from 'react'
import './App.css'
import SearchInterface from './components/SearchInterface'
import ChatInterface from './components/ChatInterface'
import SummarizeInterface from './components/SummarizeInterface'
import AdaptiveRAGInterface from './components/AdaptiveRAGInterface'
import UploadInterface from './components/UploadInterface'
import ThemeToggle from './components/ThemeToggle'
import HistorySidebar from './components/HistorySidebar' // Import HistorySidebar

function App() {
    const [activeTab, setActiveTab] = useState('adaptive-rag')
    const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')
    const [showHistory, setShowHistory] = useState(false) // Lifted state
    const [historyTrigger, setHistoryTrigger] = useState(0)
    const [sessionStats, setSessionStats] = useState({ documents: 0, chunks: 0 })

    const refreshHistory = () => {
        // Add a small delay to allow backend to finish writing to file
        setTimeout(() => {
            setHistoryTrigger(prev => prev + 1)
        }, 500)
    }

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem('theme', theme)
    }, [theme])

    const tabs = [
        { id: 'search', label: 'Semantic Search', icon: '🔍' },
        { id: 'chat', label: 'Research Chat', icon: '💬' },
        { id: 'summarize', label: 'Summarize', icon: '📄' },
        { id: 'adaptive-rag', label: 'RAG', icon: '🧠' },
        { id: 'upload', label: 'Upload', icon: '📤' }
    ]

    return (
        <div className="app" style={{ display: 'flex', flexDirection: 'row', height: '100vh', overflow: 'hidden' }}>
            <HistorySidebar
                isOpen={showHistory}
                onClose={() => setShowHistory(false)}
                refreshTrigger={historyTrigger}
            />

            <div className="app-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', height: '100%' }}>
                <header className="app-header" style={{ position: 'relative', flexShrink: 0 }}>
                    <div className="header-controls">
                        {!showHistory && (
                            <button
                                onClick={() => setShowHistory(true)}
                                title="Open History"
                                style={{
                                    padding: '0.5rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--border-color)',
                                    background: 'var(--bg-card)',
                                    color: 'var(--text-primary)',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'all 0.3s ease',
                                    boxShadow: 'var(--shadow-sm)'
                                }}
                            >
                                <span style={{ fontSize: '1.2rem' }}>📜</span>
                            </button>
                        )}
                        <ThemeToggle theme={theme} setTheme={setTheme} />
                    </div>
                    <h1>EndeeNova</h1>
                    <p>Your Intelligent document search with explainable reasoning</p>
                </header>

                <nav className="tab-nav" style={{ flexShrink: 0 }}>
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            <span className="tab-label">{tab.label}</span>
                        </button>
                    ))}
                </nav>

                <main className="app-main" style={{ flex: 1, overflowY: 'auto', width: '100%' }}>
                    {activeTab === 'search' && <SearchInterface />}
                    {activeTab === 'chat' && <ChatInterface onInteraction={refreshHistory} />}
                    {activeTab === 'summarize' && <SummarizeInterface />}
                    {activeTab === 'adaptive-rag' && <AdaptiveRAGInterface onInteraction={refreshHistory} />}
                    {activeTab === 'upload' && <UploadInterface stats={sessionStats} setStats={setSessionStats} />}
                </main>

                <footer className="app-footer" style={{ flexShrink: 0 }}>
                    <p>Powered by Endee Vector DB • OpenRouter LLM • LangGraph</p>
                </footer>
            </div>
        </div>
    )
}

export default App
