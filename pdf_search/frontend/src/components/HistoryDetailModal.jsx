import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

const formatLatex = (text) => {
    if (!text) return ''
    return text
        .replace(/\\\[/g, '$$$$') // Replace \[ with $$
        .replace(/\\\]/g, '$$$$') // Replace \] with $$
        .replace(/\\\(/g, '$$')   // Replace \( with $
        .replace(/\\\)/g, '$$')   // Replace \) with $
}

function HistoryDetailModal({ isOpen, onClose, interaction }) {
    if (!isOpen || !interaction) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            zIndex: 2000,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            backdropFilter: 'blur(4px)'
        }} onClick={onClose}>
            <div className="custom-scrollbar" style={{
                background: 'var(--bg-card)',
                padding: '2rem',
                borderRadius: '16px',
                width: '90%',
                maxWidth: '800px',
                maxHeight: '85vh',
                overflowY: 'auto',
                position: 'relative',
                boxShadow: 'var(--shadow-lg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)'
            }} onClick={e => e.stopPropagation()}>
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        background: 'none',
                        border: 'none',
                        fontSize: '1.5rem',
                        cursor: 'pointer',
                        color: 'var(--text-secondary)'
                    }}
                >
                    ✕
                </button>

                <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                    <h2 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)' }}>
                        {interaction.title || interaction.question}
                    </h2>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', gap: '1rem' }}>
                        <span>📅 {new Date(interaction.timestamp).toLocaleString()}</span>
                        {interaction.topics && interaction.topics.length > 0 && (
                            <span>🏷️ {interaction.topics.join(', ')}</span>
                        )}
                    </div>
                </div>

                <div className="markdown-content" style={{ lineHeight: '1.6' }}>
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeRaw, rehypeKatex]}
                        components={{
                            code({ node, inline, className, children, ...props }) {
                                if (inline) {
                                    return <code {...props}>{children}</code>
                                }
                                return (
                                    <pre {...props}>
                                        <code className={className}>{children}</code>
                                    </pre>
                                )
                            }
                        }}
                    >
                        {formatLatex(interaction.answer)}
                    </ReactMarkdown>
                </div>

                {/* Sources Section */}
                {interaction.sources && interaction.sources.length > 0 && (
                    <div className="sources" style={{ marginTop: '2rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
                        <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem', fontSize: '1.1rem' }}>📚 Sources</h3>
                        {interaction.sources.map((source, index) => (
                            <div key={index} className="source-item">
                                {index + 1}. {source}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default HistoryDetailModal
