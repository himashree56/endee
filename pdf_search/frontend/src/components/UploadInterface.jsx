import { useState, useEffect } from 'react'

function UploadInterface() {
    const [selectedFiles, setSelectedFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [stats, setStats] = useState({ documents: 0, chunks: 0 })

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/documents')
            const data = await response.json()
            if (data.success) {
                const totalChunks = data.documents.reduce((acc, doc) => acc + (doc.chunks || 0), 0)
                setStats({
                    documents: data.total,
                    chunks: totalChunks
                })
            }
        } catch (error) {
            console.error('Error fetching stats:', error)
        }
    }

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

    const handleUpload = async (e) => {
        e.preventDefault()
        if (selectedFiles.length === 0) return

        setUploading(true)
        setResult(null)

        try {
            const formData = new FormData()
            selectedFiles.forEach(file => {
                formData.append('files', file)
            })

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            })

            const data = await response.json()

            if (data.success) {
                setResult({
                    success: true,
                    message: data.message,
                    filenames: data.filenames
                })
                setSelectedFiles([])
                // Reset file input
                document.getElementById('file-input').value = null
                fetchStats() // Refresh stats
            } else {
                setResult({
                    success: false,
                    message: data.detail || 'Upload failed'
                })
            }
        } catch (error) {
            console.error('Error:', error)
            setResult({
                success: false,
                message: 'Error uploading files: ' + error.message
            })
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
                        disabled={uploading}
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
                    disabled={selectedFiles.length === 0 || uploading}
                >
                    {uploading ? 'Uploading & Indexing...' : 'Upload & Index'}
                </button>
            </form>

            {uploading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Uploading and indexing PDFs...</p>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        This may take a moment depending on file sizes
                    </p>
                </div>
            )}

            {result && (
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
        </div>
    )
}

export default UploadInterface
