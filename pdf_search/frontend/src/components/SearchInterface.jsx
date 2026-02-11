import { useState } from 'react'
import API_BASE_URL from '../config'

function SearchInterface({ onInteraction }) {
    const [query, setQuery] = useState('')
    const [loading, setLoading] = useState(false)
    const [results, setResults] = useState(null)

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, top_k: 5 })
            })

            const data = await response.json()
            setResults(data)
            if (data.success && onInteraction) {
                onInteraction()
            }
        } catch (error) {
            console.error('Error:', error)
            alert('Error: ' + error.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="interface">
            <h2>🔍 Semantic Search</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Search for specific information across all documents
            </p>

            <form onSubmit={handleSearch}>
                <div className="input-group">
                    <label>Search Query</label>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g., machine learning algorithms"
                        disabled={loading}
                    />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </form>

            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Searching...</p>
                </div>
            )}

            {results && results.success && (
                <div style={{ marginTop: '2rem' }}>
                    <h3>Found {results.num_results} results</h3>
                    {results.results.map((result, index) => (
                        <div key={index} className="result-card">
                            <h4>{result.file_name} - Page {result.page}</h4>
                            <p>{result.text}</p>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                Score: {result.score.toFixed(3)}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default SearchInterface
