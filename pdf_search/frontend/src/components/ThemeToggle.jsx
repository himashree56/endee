import React from 'react'

function ThemeToggle({ theme, setTheme }) {
    return (
        <div style={{
            display: 'flex',
            gap: '0.5rem',
            alignItems: 'center'
        }}>
            {[
                { id: 'light', icon: '☀️', label: 'Light' },
                { id: 'dark', icon: '🌙', label: 'Dark' },
                { id: 'neon', icon: '⚡', label: 'Neon' }
            ].map(t => (
                <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    style={{
                        background: theme === t.id ? 'var(--accent-primary)' : 'var(--bg-card)',
                        color: theme === t.id ? (theme === 'neon' ? 'var(--bg-app)' : 'white') : 'var(--text-primary)',
                        border: `1px solid ${theme === t.id ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                        padding: '0.5rem 1rem',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        boxShadow: theme === t.id ? 'var(--shadow-md)' : 'none',
                        transition: 'all 0.3s ease',
                        fontWeight: theme === t.id ? 600 : 400
                    }}
                    title={`Switch to ${t.label} Theme`}
                >
                    <span>{t.icon}</span>
                    <span style={{ fontSize: '0.9rem' }}>{t.label}</span>
                </button>
            ))}
        </div>
    )
}

export default ThemeToggle
