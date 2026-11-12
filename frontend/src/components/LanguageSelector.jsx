import React from 'react'
import { GlobeIcon, AlertCircleIcon } from './Icons'

export const LANGUAGES = [
  { code: 'en', label: 'English', speechCode: 'en-IN', reviewed: true },
  { code: 'hi', label: 'हिन्दी (Hindi)', speechCode: 'hi-IN', reviewed: false },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)', speechCode: 'gu-IN', reviewed: false }
]

export default function LanguageSelector({ currentLang, onLanguageChange, dark = false }) {
  const currentLangObj = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <GlobeIcon size={16} color={dark ? '#94a3b8' : '#64748b'} />
        <select
          value={currentLang}
          onChange={(e) => onLanguageChange(e.target.value)}
          aria-label="Select interview language"
          style={{
            flex: 1,
            padding: '7px 12px',
            borderRadius: '8px',
            border: dark ? '1px solid #334155' : '1px solid #cbd5e1',
            backgroundColor: dark ? '#1e293b' : '#ffffff',
            color: dark ? '#f1f5f9' : '#0f172a',
            fontWeight: 500,
            fontSize: '0.86rem',
            cursor: 'pointer',
            outline: 'none',
            transition: 'border-color 0.2s'
          }}
        >
          {LANGUAGES.map(lang => (
            <option key={lang.code} value={lang.code} style={{ background: dark ? '#1e293b' : '#ffffff', color: dark ? '#f1f5f9' : '#0f172a' }}>
              {lang.label}
            </option>
          ))}
        </select>
      </div>

      {!currentLangObj.reviewed && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#f59e0b', marginTop: '2px' }}>
          <AlertCircleIcon size={12} color="#f59e0b" />
          <span>Translation needs clinician review</span>
        </div>
      )}
    </div>
  )
}
