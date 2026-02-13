import { useState, useEffect } from 'react'
import API_BASE_URL from '../config'

function UploadInterface() {
    const [selectedFiles, setSelectedFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [stats, setStats] = useState({ documents: 0, chunks: 0 })
    const [documents, setDocuments] = useState([])

    const fetchStats = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/documents`)
            const data = await response.json()
            if (data.success) {
                const totalChunks = data.documents.reduce((acc, doc) => acc + (doc.chunks || 0), 0)
                setStats({
                    documents: data.total,
                    chunks: totalChunks
                })
                setDocuments(data.documents)
            }
        } catch (error) {
            console.error('Error fetching stats:', error)
        }
    }

    const handleDelete = async (filename) => {
        if (!confirm(`Are you sure you want to delete "${filename}"? This cannot be undone.`)) return

        try {
            const response = await fetch(`${API_BASE_URL}/api/documents/${filename}`, {
                method: 'DELETE'
            })
            const data = await response.json()

            if (response.ok) {
                alert("Document deleted successfully")
                fetchStats() // Refresh list
            } else {
                alert("Failed to delete: " + (data.detail || "Unknown error"))
            }
        } catch (error) {
            console.error("Delete error:", error)
            alert("Error deleting document")
        }
    }

    // Fetch total stats on mount
    useEffect(() => {
        fetchStats()
    }, [])


    const handleFileChange = (e) => {
        const files = Array.from(e.target.files).filter(file => file.type === 'application/pdf')

        if (files.length > 0) {
            setSelectedFiles(files)
            setResult(null)
        } else {
            alert('Please select PDF files')
            e.target.value = null
        }
    }

    const [ingestionStatus, setIngestionStatus] = useState(null)

    const pollStatus = async (filenames) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/ingestion/status`)
                const data = await res.json()
                // console.log("Poll data:", data) // Uncomment for debugging

                if (data.success && data.status) {
                    const statuses = filenames.map(name => data.status[name]).filter(Boolean)
                    const allCompleted = statuses.every(s => s.status === 'completed' || s.status === 'failed')

                    // Calculate total progress
                    const totalProgress = statuses.reduce((acc, s) => acc + (s.progress || 0), 0)

                    setIngestionStatus({
                        active: !allCompleted,
                        items: statuses
                    })

                    if (allCompleted) {
                        clearInterval(interval)

                        // Update session stats
                        const newDocs = statuses.filter(s => s.status === 'completed').length
                        const newChunks = statuses.reduce((acc, s) => acc + (s.total || 0), 0)

                        setStats(prev => ({
                            documents: prev.documents + newDocs,
                            chunks: prev.chunks + newChunks
                        }))

                        setIngestionStatus(null)
                        // Update result message
                        const allSuccess = statuses.every(s => s.status === 'completed')
                        if (allSuccess) {
                            setResult(prev => ({ ...prev, message: "✅ Upload & Ingestion Complete!" }))
                        } else {
                            setResult(prev => ({ ...prev, message: "⚠️ Upload complete, but some files failed ingestion." }))
                        }
                    }
                }
            } catch (err) {
                console.error("Polling error:", err)
            }
        }, 1000)
    }

    const handleUpload = async (e) => {
        e.preventDefault()
        if (selectedFiles.length === 0) return

        setUploading(true)
        setResult(null)
        setIngestionStatus({ active: true, items: [] })

        try {
            const formData = new FormData()
            selectedFiles.forEach(file => {
                formData.append('files', file)
            })

            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData
            })

            const data = await response.json()

            if (data.success) {
                setResult({
                    success: true,
                    message: "Upload successful. Starting ingestion...",
                    filenames: data.filenames
                })
                setSelectedFiles([])
                document.getElementById('file-input').value = null

                // Start polling
                pollStatus(data.filenames)

            } else {
                setResult({
                    success: false,
                    message: data.detail || 'Upload failed'
                })
                setIngestionStatus(null)
            }
        } catch (error) {
            console.error('Error:', error)
            setResult({
                success: false,
                message: 'Error uploading files: ' + error.message
            })
            setIngestionStatus(null)
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="interface">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h2>📤 Upload PDFs</h2>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                        Upload multiple PDF documents to index and search
                    </p>
                </div>
                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    background: 'var(--bg-secondary)',
                    padding: '0.5rem 1rem',
                    borderRadius: '12px',
                    border: '1px solid var(--border-color)'
                }}>
                    <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block' }}>DOCUMENTS</span>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{stats.documents}</span>
                    </div>
                    <div style={{ width: '1px', background: 'var(--border-color)' }}></div>
                    <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block' }}>CHUNKS</span>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-secondary)' }}>{stats.chunks}</span>
                    </div>
                </div>
            </div>

            <form onSubmit={handleUpload}>
                <div className="input-group">
                    <label>Select PDF Files</label>
                    <input
                        id="file-input"
                        type="file"
                        accept=".pdf"
                        multiple
                        onChange={handleFileChange}
                        disabled={uploading || (ingestionStatus && ingestionStatus.active)}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            border: '2px dashed var(--accent-primary)',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            backgroundColor: 'var(--bg-secondary)',
                            color: 'var(--text-primary)'
                        }}
                    />
                </div>

                {selectedFiles.length > 0 && (
                    <div style={{
                        padding: '1rem',
                        background: 'var(--bg-secondary)',
                        borderRadius: '8px',
                        marginBottom: '1rem',
                        color: 'var(--text-primary)'
                    }}>
                        <p><strong>Selected {selectedFiles.length} files:</strong></p>
                        <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem', fontSize: '0.9rem' }}>
                            {selectedFiles.map((file, i) => (
                                <li key={i}>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</li>
                            ))}
                        </ul>
                    </div>
                )}

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={selectedFiles.length === 0 || uploading || (ingestionStatus && ingestionStatus.active)}
                >
                    {uploading ? 'Uploading...' : (ingestionStatus && ingestionStatus.active ? 'Ingesting...' : 'Upload & Index')}
                </button>
            </form>

            {/* Ingestion Progress UI */}
            {ingestionStatus && ingestionStatus.active && (
                <div className="loading" style={{ marginTop: '1rem', textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div className="spinner"></div>
                        <strong>Processing documents...</strong>
                    </div>
                    <div style={{ marginTop: '0.5rem' }}>
                        {ingestionStatus.items.map((item, i) => (
                            <div key={i} style={{ fontSize: '0.9rem', marginBottom: '5px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>{item.message || 'Processing...'}</span>
                                    <span style={{ fontWeight: 'bold' }}>{item.progress} chunks processed</span>
                                </div>
                                <div style={{ width: '100%', background: '#eee', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                                    <div style={{
                                        width: item.total ? `${Math.min(100, (item.progress / item.total) * 100)}%` : '50%',
                                        background: item.status === 'failed' ? 'red' : 'var(--accent-primary)',
                                        height: '100%',
                                        transition: 'width 0.5s ease'
                                    }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {result && !ingestionStatus && (
                <div style={{ marginTop: '2rem' }}>
                    <div
                        className="result-card"
                        style={{
                            borderLeftColor: result.success ? '#4caf50' : '#f44336'
                        }}
                    >
                        <h3>{result.success ? '✅ Success!' : '❌ Error'}</h3>
                        <p>{result.message}</p>
                        {result.success && result.filenames && (
                            <div style={{ marginTop: '1rem' }}>
                                <p><strong>Indexed files:</strong></p>
                                <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem', fontSize: '0.9rem' }}>
                                    {result.filenames.map((name, i) => (
                                        <li key={i}>{name}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div style={{
                marginTop: '2rem',
                padding: '1rem',
                background: 'var(--bg-secondary)',
                borderRadius: '8px',
                color: 'var(--text-primary)'
            }}>
                <h3 style={{ marginBottom: '0.5rem' }}>ℹ️ How it works</h3>
                <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
                    <li>Select one or more PDF files</li>
                    <li>Files will be uploaded and processed in batch</li>
                    <li>Text extraction and indexing happens automatically</li>
                    <li>You can search across all uploaded documents</li>
                </ul>
            </div>

            {/* Document Management Section */}
            <div style={{
                marginTop: '2rem',
                padding: '1rem',
                background: 'var(--bg-secondary)',
                borderRadius: '8px',
                color: 'var(--text-primary)'
            }}>
                <h3 style={{ marginBottom: '1rem' }}>📚 Indexed Documents</h3>
                {stats.documents === 0 ? (
                    <p style={{ color: 'var(--text-secondary)' }}>No documents indexed yet.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                        {documents.map((doc, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '0.8rem',
                                background: 'var(--bg-app)',
                                borderRadius: '6px',
                                border: '1px solid var(--border-color)'
                            }}>
                                <div>
                                    <div style={{ fontWeight: 'bold' }}>{doc.filename}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {doc.chunks} chunks • {doc.pages} pages
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(doc.filename)}
                                    style={{
                                        background: '#ffebee',
                                        color: '#d32f2f',
                                        border: '1px solid #ffcdd2',
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '0.9rem'
                                    }}
                                    title="Delete Document"
                                >
                                    🗑️ Delete
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default UploadInterface
