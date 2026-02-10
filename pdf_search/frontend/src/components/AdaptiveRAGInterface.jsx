import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import 'katex/dist/katex.min.css'
import API_BASE_URL from '../config'

function AdaptiveRAGInterface() {
    const [question, setQuestion] = useState('')
    const [mode, setMode] = useState('standard') // 'standard' or 'insight'
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)

    const formatLatex = (text) => {
        if (!text) return ''
        return text
            .replace(/\\\[/g, '$$$$')
            .replace(/\\\]/g, '$$$$')
            .replace(/\\\(/g, '$$')
            .replace(/\\\)/g, '$$')
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!question.trim()) return

        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/api/adaptive-rag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, mode })
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div>
                    <h2>🧠 Adaptive Reasoning RAG</h2>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                        {mode === 'standard'
                            ? "Ask complex questions and see the AI's reasoning process"
                            : "Generate deep strategic insights and hidden patterns from documents"}
                    </p>
                </div>
            </div>

            <div className="mode-selector" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
                <button
                    onClick={() => setMode('standard')}
                    style={{
                        padding: '0.5rem 1rem',
                        borderRadius: '20px',
                        border: '1px solid var(--border-color)',
                        background: mode === 'standard' ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                        color: mode === 'standard' ? 'white' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        fontWeight: 600
                    }}
                >
                    🔍 Standard Reasoning
                </button>
                <button
                    onClick={() => setMode('insight')}
                    style={{
                        padding: '0.5rem 1rem',
                        borderRadius: '20px',
                        border: '1px solid var(--border-color)',
                        background: mode === 'insight' ? 'var(--accent-secondary)' : 'var(--bg-secondary)',
                        color: mode === 'insight' ? 'white' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        fontWeight: 600
                    }}
                >
                    ✨ Deep Insight Generator
                </button>
            </div>

            <form onSubmit={handleSubmit}>
                <div className="input-group">
                    <label>Your Question</label>
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="e.g., What are the main challenges in building agentic AI systems?"
                        rows={3}
                        disabled={loading}
                    />
                </div>

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                    style={{ background: mode === 'insight' ? 'linear-gradient(135deg, #9c27b0 0%, #673ab7 100%)' : undefined }}
                >
                    {loading ? 'Thinking...' : mode === 'insight' ? 'Generate Insights' : 'Ask Question'}
                </button>
            </form>

            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Running adaptive reasoning...</p>
                </div>
            )}

            {result && result.success && (
                <div style={{ marginTop: '2rem' }}>
                    {/* Query Analysis */}
                    <div className="result-card">
                        <h3>📊 Query Analysis</h3>
                        <p><strong>Complexity:</strong> {result.query_analysis?.complexity || 'N/A'}</p>
                        <p><strong>Type:</strong> {result.query_analysis?.query_type || 'N/A'}</p>
                    </div>

                    {/* Reasoning Steps */}
                    <div className="reasoning-steps">
                        <h3>🧠 Reasoning Process</h3>
                        {result.reasoning_steps?.map((step, index) => (
                            <div key={index} className="step">
                                <div className="step-icon">
                                    {index === 0 ? '🔍' : index === result.reasoning_steps.length - 1 ? '✅' : '⚙️'}
                                </div>
                                <div className="step-content">
                                    <h4>{step.step}</h4>
                                    <p>{step.details}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Answer with Reliability Badge */}
                    <div className="result-card" style={{ borderLeftColor: result.truth_label === 'well-supported' ? '#4caf50' : result.truth_label === 'disputed' ? '#f44336' : '#ff9800' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3>💡 Answer</h3>
                            {result.truth_label && (
                                <span style={{
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '16px',
                                    fontSize: '0.85rem',
                                    fontWeight: 600,
                                    textTransform: 'uppercase',
                                    backgroundColor: result.truth_label === 'well-supported' ? '#e8f5e9' : result.truth_label === 'disputed' ? '#ffebee' : '#fff3e0',
                                    color: result.truth_label === 'well-supported' ? '#2e7d32' : result.truth_label === 'disputed' ? '#c62828' : '#ef6c00',
                                    border: `1px solid ${result.truth_label === 'well-supported' ? '#a5d6a7' : result.truth_label === 'disputed' ? '#ef9a9a' : '#ffcc80'}`
                                }}>
                                    {result.truth_label.replace('-', ' ')}
                                </span>
                            )}
                            {result.confidence_score && (
                                <span style={{
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '16px',
                                    fontSize: '0.85rem',
                                    fontWeight: 600,
                                    backgroundColor: result.confidence_score >= 0.8 ? '#e8f5e9' : result.confidence_score >= 0.5 ? '#fff3e0' : '#ffebee',
                                    color: result.confidence_score >= 0.8 ? '#2e7d32' : result.confidence_score >= 0.5 ? '#ef6c00' : '#c62828',
                                    border: `1px solid ${result.confidence_score >= 0.8 ? '#a5d6a7' : result.confidence_score >= 0.5 ? '#ffcc80' : '#ef9a9a'}`
                                }}>
                                    Confidence: {Math.round(result.confidence_score * 100)}%
                                </span>
                            )}
                        </div>
                        <div className="markdown-content" style={{ fontSize: '0.95rem', lineHeight: '1.6' }}>
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeRaw, rehypeKatex]}
                            >
                                {formatLatex(result.answer)}
                            </ReactMarkdown>
                        </div>
                    </div>

                    {/* Reliability & Critique Report */}
                    {result.critique_report && (
                        <div className="result-card" style={{ background: 'var(--bg-secondary)', borderLeft: '4px solid var(--accent-secondary)' }}>
                            <h3>⚖️ Truth & Reliability Check</h3>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                <div>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Evidence Strength</p>
                                    <p style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>{result.reliability_score?.evidence_strength || 'N/A'}</p>
                                </div>
                                <div>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Consensus</p>
                                    <p style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>{result.reliability_score?.consensus || 'N/A'}</p>
                                </div>
                            </div>

                            {result.critique_report.missing_context?.length > 0 && (
                                <div style={{ marginBottom: '0.5rem' }}>
                                    <p style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f57c00' }}>⚠️ Missing Context:</p>
                                    <ul style={{ margin: '0.25rem 0', paddingLeft: '1.5rem', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                                        {result.critique_report.missing_context.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                            )}

                            {result.critique_report.assumptions_made?.length > 0 && (
                                <div style={{ marginBottom: '0.5rem' }}>
                                    <p style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1976d2' }}>🤔 Assumptions Made:</p>
                                    <ul style={{ margin: '0.25rem 0', paddingLeft: '1.5rem', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                                        {result.critique_report.assumptions_made.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Confidence */}
                    <div className="confidence-meter">
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>🎯 System Confidence:</span>
                        <div className="confidence-bar">
                            <div
                                className="get-fill"
                                style={{
                                    width: `${result.confidence * 100}%`,
                                    background: 'var(--accent-gradient)'
                                }}
                            />
                        </div>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {(result.confidence * 100).toFixed(0)}%
                        </span>
                    </div>

                    {/* Sources */}
                    {result.sources && result.sources.length > 0 && (
                        <div className="sources">
                            <h3>📚 Sources</h3>
                            {result.sources.map((source, index) => (
                                <div key={index} className="source-item">
                                    {index + 1}. {source}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Retrieval Iterations */}
                    {result.retrieval_iterations && result.retrieval_iterations.length > 1 && (
                        <div className="result-card">
                            <h3>🔄 Retrieval Iterations</h3>
                            {result.retrieval_iterations.map((iteration, index) => (
                                <p key={index}>
                                    <strong>Iteration {iteration.iteration}:</strong> {iteration.num_results} documents
                                    (avg score: {iteration.avg_score.toFixed(3)})
                                </p>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default AdaptiveRAGInterface
