import React from 'react'

export const LANGUAGES = [
  { code: 'en', label: 'English', speechCode: 'en-IN', reviewed: true },
  { code: 'hi', label: 'हिन्दी (Hindi)', speechCode: 'hi-IN', reviewed: false },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)', speechCode: 'gu-IN', reviewed: false }
]

export default function LanguageSelector({ currentLang, onLanguageChange }) {
  const currentLangObj = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>🌐</span>
        <select
          value={currentLang}
          onChange={(e) => onLanguageChange(e.target.value)}
          aria-label="Select interview language"
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1.5px solid var(--border-strong)',
            backgroundColor: '#ffffff',
            fontWeight: 600,
            fontSize: '0.9rem',
            cursor: 'pointer'
          }}
        >
          {LANGUAGES.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.label}
            </option>
          ))}
        </select>
      </div>

      {!currentLangObj.reviewed && (
        <span style={{ fontSize: '0.72rem', color: 'var(--warning-amber)', fontWeight: 500 }}>
          ⚠️ Translation needs clinician review
        </span>
      )}
    </div>
  )
}
