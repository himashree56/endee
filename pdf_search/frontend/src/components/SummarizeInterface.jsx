import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import API_BASE_URL from '../config'

function SummarizeInterface() {
    const [documents, setDocuments] = useState([])
    const [selectedDoc, setSelectedDoc] = useState('')
    const [length, setLength] = useState('medium')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)

    useEffect(() => {
        fetchDocuments()
    }, [])

    const fetchDocuments = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/documents`)
            const data = await response.json()

            if (data.success) {
                setDocuments(data.documents)
                if (data.documents.length > 0) {
                    setSelectedDoc(data.documents[0].filename)
                }
            }
        } catch (error) {
            console.error('Error fetching documents:', error)
        }
    }

    const handleSummarize = async (e) => {
        e.preventDefault()
        if (!selectedDoc) return

        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/api/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: selectedDoc, length })
            })

            const data = await response.json()
            setResult(data)
        } catch (error) {
            console.error('Error:', error)
            alert('Error: ' + error.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="interface">
            <h2>📄 Document Summarization</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Generate summaries of indexed documents
            </p>

            <form onSubmit={handleSummarize}>
                <div className="input-group">
                    <label>Select Document</label>
                    <select
                        value={selectedDoc}
                        onChange={(e) => setSelectedDoc(e.target.value)}
                        style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '2px solid var(--border-color)', background: 'var(--bg-input)', color: 'var(--text-primary)' }}
                        disabled={loading}
                    >
                        {documents.map(doc => (
                            <option key={doc.filename} value={doc.filename}>
                                {doc.filename} ({doc.chunks} chunks, {doc.pages} pages)
                            </option>
                        ))}
                    </select>
                </div>

                <div className="input-group">
                    <label>Summary Length</label>
                    <select
                        value={length}
                        onChange={(e) => setLength(e.target.value)}
                        style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '2px solid var(--border-color)', background: 'var(--bg-input)', color: 'var(--text-primary)' }}
                        disabled={loading}
                    >
                        <option value="short">Short (2-3 sentences)</option>
                        <option value="medium">Medium (1-2 paragraphs)</option>
                        <option value="long">Long (detailed)</option>
                    </select>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading || !selectedDoc}>
                    {loading ? 'Summarizing...' : 'Generate Summary'}
                </button>
            </form>

            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Generating summary...</p>
                </div>
            )}

            {result && result.success && result.summary && (
                <div style={{ marginTop: '2rem' }}>
                    <div className="result-card">
                        <h3>📄 {result.summary.filename}</h3>
                        <p><strong>Chunks:</strong> {result.summary.chunk_count} | <strong>Pages:</strong> {result.summary.page_count}</p>
                    </div>

                    <div className="result-card" style={{ borderLeftColor: '#4caf50' }}>
                        <h3>📝 Summary</h3>
                        <p style={{ whiteSpace: 'pre-wrap' }}>{result.summary.summary}</p>
                    </div>
                </div>
            )}
        </div>
    )
}

export default SummarizeInterface
