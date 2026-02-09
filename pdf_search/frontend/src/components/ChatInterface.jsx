import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

function ChatInterface() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your research assistant. Ask me anything about your documents.' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const chatEndRef = useRef(null)

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    const formatLatex = (text) => {
        if (!text) return ''
        return text
            .replace(/\\\[/g, '$$$$') // Replace \[ with $$
            .replace(/\\\]/g, '$$$$') // Replace \] with $$
            .replace(/\\\(/g, '$$')   // Replace \( with $
            .replace(/\\\)/g, '$$')   // Replace \) with $
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            // Prepare history for API (exclude current message as it is sent in 'question')
            const history = messages.map(m => ({ role: m.role, content: m.content }))

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: userMessage.content,
                    history: history
                })
            })

            const data = await response.json()

            if (data.success) {
                const aiMessage = {
                    role: 'assistant',
                    content: data.answer,
                    sources: data.sources
                }
                setMessages(prev => [...prev, aiMessage])
            } else {
                throw new Error(data.detail || 'Failed to get answer')
            }
        } catch (error) {
            console.error('Error:', error)
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="interface" style={{
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100vh - 180px)', // Adjust based on header/footer
            padding: 0,
            overflow: 'hidden'
        }}>
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.5rem'
            }}>
                {messages.map((msg, index) => (
                    <div key={index} className={`chat-message ${msg.role}`}>
                        <div className={`chat-bubble ${msg.role}`}>
                            {msg.role === 'assistant' ? (
                                <div className="markdown-content" style={{ fontSize: '0.95rem' }}>
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm, remarkMath]}
                                        rehypePlugins={[rehypeRaw, rehypeKatex]}
                                    >
                                        {formatLatex(msg.content)}
                                    </ReactMarkdown>

                                    {msg.sources && msg.sources.length > 0 && (
                                        <div style={{ marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-color)' }}>
                                            <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>📚 Sources:</p>
                                            <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                {msg.sources.map((s, i) => (
                                                    <li key={i}>{s}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div style={{
                            padding: '1rem 1.5rem',
                            backgroundColor: '#f8f9fa',
                            borderRadius: '16px',
                            borderTopLeftRadius: '4px',
                            color: '#666'
                        }}>
                            <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div style={{
                padding: '1.5rem',
                background: 'white',
                borderTop: '1px solid #eee'
            }}>
                <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem' }}>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your question..."
                        disabled={loading}
                        style={{
                            flex: 1,
                            padding: '1rem',
                            borderRadius: '24px',
                            border: '1px solid #e0e0e0',
                            fontSize: '1rem',
                            outline: 'none'
                        }}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        style={{
                            width: '50px',
                            height: '50px',
                            borderRadius: '50%',
                            border: 'none',
                            background: loading || !input.trim() ? '#e0e0e0' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.2rem',
                            transition: 'all 0.3s ease'
                        }}
                    >
                        ➤
                    </button>
                </form>
            </div>
        </div>
    )
}

export default ChatInterface
