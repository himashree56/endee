import { useState, useEffect } from 'react'
import HistoryDetailModal from './HistoryDetailModal'
import API_BASE_URL from '../config'


function HistorySidebar({ isOpen, onClose, refreshTrigger }) {
    const [history, setHistory] = useState(null)
    const [loading, setLoading] = useState(false)
    const [selectedItem, setSelectedItem] = useState(null)
    const [editingId, setEditingId] = useState(null)
    const [editTitle, setEditTitle] = useState("")

    const [error, setError] = useState(null)

    const fetchHistory = async () => {
        console.log("[HistorySidebar] Fetching history...")
        setLoading(true)
        setError(null)
        try {
            const url = `${API_BASE_URL}/api/history`
            console.log(`[HistorySidebar] GET ${url}`)
            const response = await fetch(url)
            const data = await response.json()
            console.log("[HistorySidebar] Data received:", data)

            if (data.success) {
                setHistory(data.history)
            } else {
                console.error("[HistorySidebar] API returned success: false")
                setError("API Error: " + (data.message || "Unknown error"))
            }
        } catch (error) {
            console.error("Failed to fetch history", error)
            setError(error.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isOpen) {
            fetchHistory()
        }
    }, [isOpen, refreshTrigger])

    const handleClearHistory = async () => {
        if (!confirm("Are you sure you want to clear ALL history? This cannot be undone.")) return
        try {
            const response = await fetch(`${API_BASE_URL}/api/history`, { method: 'DELETE' })
            if (response.ok) {
                fetchHistory()
            }
        } catch (e) {
            console.error("Failed to clear history", e)
        }
    }

    const handleDelete = async (e, id) => {
        e.stopPropagation()
        if (!confirm("Delete this interaction?")) return
        try {
            const res = await fetch(`${API_BASE_URL}/api/history/${id}`, { method: 'DELETE' })
            if (res.ok) {
                fetchHistory()
            }
        } catch (e) {
            console.error("Failed to delete item", e)
        }
    }

    const startEdit = (e, item) => {
        e.stopPropagation()
        setEditingId(item.id)
        setEditTitle(item.title || item.question)
    }

    const saveEdit = async (e, id) => {
        e.stopPropagation()
        try {
            const res = await fetch(`${API_BASE_URL}/api/history/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: editTitle })
            })
            if (res.ok) {
                setEditingId(null)
                fetchHistory()
            }
        } catch (e) {
            console.error("Failed to rename item", e)
        }
    }

    const cancelEdit = (e) => {
        e.stopPropagation()
        setEditingId(null)
    }

    // We don't return null anymore, instead render with width 0
    // if (!isOpen) return null

    return (
        <>
            <div className={`history-sidebar ${isOpen ? 'open' : 'closed'}`}>
                {/* Navbar Section (Fixed) */}
                <div style={{ padding: '1.5rem 1rem 1rem 1rem', borderBottom: '1px solid var(--border-color)', minWidth: '300px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h2 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-primary)' }}>📜 History</h2>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            {(history?.interactions?.length > 0 || history?.topics_explored?.length > 0) && (
                                <button
                                    onClick={handleClearHistory}
                                    title="Clear All"
                                    style={{ background: 'none', border: 'none', color: '#e53e3e', cursor: 'pointer', fontSize: '1.2rem' }}
                                >
                                    🗑️
                                </button>
                            )}
                            <button
                                onClick={onClose}
                                style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--text-secondary)' }}
                            >
                                ✕
                            </button>
                        </div>
                    </div>

                    {!loading && history?.topics_explored?.length > 0 && (
                        <div style={{ marginBottom: '0.5rem' }}>
                            <h3 style={{ fontSize: '1rem', color: 'var(--accent-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                🧠 Explored Topics
                            </h3>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', maxHeight: '100px', overflowY: 'auto', paddingRight: '4px' }}>
                                {history.topics_explored.map((topic, i) => (
                                    <span key={i} style={{
                                        background: 'var(--bg-app)',
                                        color: 'var(--text-secondary)',
                                        padding: '0.2rem 0.6rem',
                                        borderRadius: '12px',
                                        fontSize: '0.75rem',
                                        border: '1px solid var(--border-color)'
                                    }}>
                                        {topic}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Scrollable Interaction List */}
                <div className="history-sidebar-content" style={{ flex: 1, overflowY: 'auto', padding: '1rem', minWidth: '300px' }}>
                    {error ? (
                        <div style={{ color: 'red', padding: '1rem', textAlign: 'center' }}>
                            <p>⚠️ Error loading history</p>
                            <small>{error}</small>
                            <button onClick={fetchHistory} style={{ marginTop: '0.5rem' }}>Retry</button>
                        </div>
                    ) : loading ? (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>Loading history...</div>
                    ) : !history || !history.interactions?.length ? (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No history found.</div>
                    ) : (
                        <div>
                            <h3 style={{ fontSize: '1rem', color: 'var(--accent-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                🕒 Recent Interactions
                            </h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {history.interactions.slice().reverse().map((item, i) => (
                                    <div key={item.id || i}
                                        onClick={() => setSelectedItem(item)}
                                        className="history-item"
                                    >
                                        <div className="history-item-date">
                                            {new Date(item.timestamp).toLocaleString()}
                                        </div>

                                        {editingId === item.id ? (
                                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }} onClick={e => e.stopPropagation()}>
                                                <input
                                                    value={editTitle}
                                                    onChange={e => setEditTitle(e.target.value)}
                                                    style={{ flex: 1, padding: '0.25rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-input)', color: 'var(--text-primary)' }}
                                                    autoFocus
                                                />
                                                <button onClick={(e) => saveEdit(e, item.id)}>💾</button>
                                                <button onClick={cancelEdit}>❌</button>
                                            </div>
                                        ) : (
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '0.5rem' }}>
                                                <p className="history-item-title" style={{ wordBreak: 'break-word', whiteSpace: 'normal' }}>
                                                    {item.title || item.question}
                                                </p>
                                                <div className="actions" style={{ display: 'flex', gap: '0.3rem', flexShrink: 0 }}>
                                                    <button onClick={(e) => startEdit(e, item)} title="Rename" style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '2px' }}>✏️</button>
                                                    <button onClick={(e) => handleDelete(e, item.id)} title="Delete" style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '2px' }}>🗑️</button>
                                                </div>
                                            </div>
                                        )}

                                        <div className="history-item-preview" style={{ wordBreak: 'break-word', whiteSpace: 'normal' }}>
                                            {item.answer}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>


            <HistoryDetailModal
                isOpen={!!selectedItem}
                onClose={() => setSelectedItem(null)}
                interaction={selectedItem}
            />
        </>
    )
}

export default HistorySidebar
