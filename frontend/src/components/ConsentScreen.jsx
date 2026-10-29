import React, { useState } from 'react'

export default function ConsentScreen({ onStartSession, onResumeSession, currentLang }) {
  const [agreed, setAgreed] = useState(false)
  const [researchConsent, setResearchConsent] = useState(false)
  const [resumeCode, setResumeCode] = useState('')
  const [resumeError, setResumeError] = useState('')
  const [isResuming, setIsResuming] = useState(false)

  const handleResume = (e) => {
    e.preventDefault()
    if (!resumeCode.trim()) {
      setResumeError('Please enter a session code')
      return
    }
    setResumeError('')
    onResumeSession(resumeCode.trim().toUpperCase())
  }

  return (
    <div style={{ maxWidth: '640px', margin: '40px auto', padding: '24px' }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        padding: '32px',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-subtle)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            color: 'var(--primary)'
          }}>
            📋
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)' }}>
              MigraineAssist Intake
            </h1>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Clinical Headache Intake & Screening Aid
            </p>
          </div>
        </div>

        {/* Clinical Disclaimer Banner */}
        <div style={{
          backgroundColor: 'var(--warning-amber-light)',
          borderLeft: '4px solid var(--warning-amber)',
          padding: '12px 16px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '20px'
        }}>
          <p style={{ fontSize: '0.88rem', color: 'var(--warning-amber)', fontWeight: 600 }}>
            Important Clinical Notice:
          </p>
          <p style={{ fontSize: '0.85rem', color: '#78350f', marginTop: '4px' }}>
            This system is an automated intake questionnaire designed to assist your treating physician. It does <b>NOT</b> diagnose medical conditions, prescribe medication, or substitute for emergency care.
          </p>
        </div>

        {/* Consent Details */}
        <div style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.9rem',
          color: 'var(--text-main)',
          marginBottom: '20px',
          lineHeight: '1.6'
        }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
            Before you begin:
          </h3>
          <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li><b>Structured Interview:</b> You will answer questions about your headache history and symptoms.</li>
            <li><b>Multilingual & Voice:</b> You may answer by voice, by tapping choices, or by typing in English, Hindi, or Gujarati.</li>
            <li><b>Physician In-The-Loop:</b> A full clinical report will be prepared for your doctor to review, confirm, and discuss with you.</li>
            <li><b>Emergency Safeguard:</b> If any dangerous neurological red flag is detected, the interview will pause immediately and guide you to emergency care.</li>
            <li><b>Privacy by Design:</b> Your answers are linked only to an anonymous 6-character participant code. No names or phone numbers are collected.</li>
          </ul>
        </div>

        {/* Checkboxes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              style={{ width: '18px', height: '18px', marginTop: '3px', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>
              I understand that this is a clinical intake tool and not a diagnosis, and I agree to proceed. <span style={{ color: 'var(--urgent-red)' }}>*</span>
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={researchConsent}
              onChange={(e) => setResearchConsent(e.target.checked)}
              style={{ width: '18px', height: '18px', marginTop: '3px', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Optional: I consent to having my fully anonymized symptom answers included in headache research datasets to help improve neurological care.
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <button
          className="btn btn-primary"
          disabled={!agreed}
          onClick={() => onStartSession(researchConsent)}
          style={{ width: '100%', padding: '14px', fontSize: '1.1rem' }}
        >
          Begin Intake Interview →
        </button>

        {/* Resume Session Block */}
        <div style={{ marginTop: '28px', borderTop: '1px solid var(--border-subtle)', paddingTop: '20px' }}>
          <button
            type="button"
            onClick={() => setIsResuming(!isResuming)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary)',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            {isResuming ? '− Hide Session Resume' : '+ Have a session code? Resume where you left off'}
          </button>

          {isResuming && (
            <form onSubmit={handleResume} style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="e.g. MIG782"
                value={resumeCode}
                onChange={(e) => setResumeCode(e.target.value.toUpperCase())}
                maxLength={8}
                className="text-input"
                style={{ maxWidth: '160px', textTransform: 'uppercase', letterSpacing: '1px' }}
              />
              <button type="submit" className="btn btn-secondary">
                Resume Session
              </button>
            </form>
          )}
          {resumeError && (
            <p style={{ color: 'var(--urgent-red)', fontSize: '0.85rem', marginTop: '6px' }}>
              {resumeError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
