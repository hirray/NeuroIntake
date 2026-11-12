import React, { useState } from 'react'
import {
  BrainIcon,
  ShieldAlertIcon,
  CheckCircleIcon,
  ActivityIcon,
  FileTextIcon,
  ChevronRightIcon
} from './Icons'

export default function ConsentScreen({ onStartSession, onResumeSession, currentLang }) {
  const [agreed, setAgreed] = useState(false)
  const [researchConsent, setResearchConsent] = useState(false)
  const [resumeCode, setResumeCode] = useState('')
  const [resumeError, setResumeError] = useState('')

  const handleResume = (e) => {
    e.preventDefault()
    if (!resumeCode.trim()) {
      setResumeError('Please enter your 6-character session code')
      return
    }
    setResumeError('')
    onResumeSession(resumeCode.trim().toUpperCase())
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      backgroundImage: 'radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(15, 118, 110, 0.15) 0px, transparent 50%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '32px 16px'
    }}>
      <div style={{
        maxWidth: '680px',
        width: '100%',
        backgroundColor: '#ffffff',
        borderRadius: '20px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
        border: '1px solid rgba(226, 232, 240, 0.8)',
        overflow: 'hidden'
      }}>
        {/* Top Header Banner */}
        <div style={{
          backgroundColor: '#1e293b',
          padding: '28px 32px',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #334155'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.4)'
            }}>
              <BrainIcon size={26} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#ffffff', margin: 0 }}>
                MigraineAssist AI
              </h1>
              <p style={{ fontSize: '0.86rem', color: '#94a3b8', margin: '2px 0 0 0' }}>
                Clinical Headache Intake & Screening Decision-Support Aid
              </p>
            </div>
          </div>
          <span style={{
            fontSize: '0.75rem',
            padding: '4px 10px',
            borderRadius: '9999px',
            backgroundColor: '#0f172a',
            color: '#60a5fa',
            border: '1px solid #3b82f6',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            ICHD-3 Protocol
          </span>
        </div>

        <div style={{ padding: '32px' }}>
          {/* Clinical Disclaimer Box */}
          <div style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderLeft: '5px solid #d97706',
            borderRadius: '12px',
            padding: '16px 18px',
            marginBottom: '24px',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start'
          }}>
            <ShieldAlertIcon size={22} color="#d97706" className="flex-shrink-0" />
            <div>
              <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#92400e', margin: 0 }}>
                Important Clinical & Safety Disclaimer
              </p>
              <p style={{ fontSize: '0.84rem', color: '#78350f', margin: '4px 0 0 0', lineHeight: 1.55 }}>
                This automated system conducts structured clinical intake for your doctor. It does <b>NOT</b> diagnose conditions, prescribe medications, or replace emergency care. In an acute emergency, call <b>112</b> or <b>108</b> immediately.
              </p>
            </div>
          </div>

          {/* Key Principles Checklist */}
          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '14px',
            padding: '20px',
            marginBottom: '26px'
          }}>
            <p style={{ fontSize: '0.92rem', fontWeight: 600, color: '#1e293b', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ActivityIcon size={18} color="#2563eb" />
              What to expect during intake:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.86rem', color: '#334155', lineHeight: 1.5 }}>
                <CheckCircleIcon size={16} color="#059669" />
                <span><b>Structured Interview:</b> 15–20 guided clinical questions assessing headache traits, duration, aura, and triggers.</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.86rem', color: '#334155', lineHeight: 1.5 }}>
                <CheckCircleIcon size={16} color="#059669" />
                <span><b>Multimodal Voice & Text:</b> Speak naturally in English, Hindi, or Gujarati, or tap quick option buttons.</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.86rem', color: '#334155', lineHeight: 1.5 }}>
                <CheckCircleIcon size={16} color="#059669" />
                <span><b>Physician Summary PDF:</b> Generates a structured clinical report for your treating neurologist or physician.</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '0.86rem', color: '#334155', lineHeight: 1.5 }}>
                <CheckCircleIcon size={16} color="#059669" />
                <span><b>Anonymous & Encrypted:</b> Identified only by an anonymous 6-letter participant code. No names or phone numbers stored.</span>
              </div>
            </div>
          </div>

          {/* Consent Checkboxes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '28px' }}>
            <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', userSelect: 'none' }}>
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                style={{ width: '19px', height: '19px', marginTop: '2px', accentColor: '#2563eb', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.92rem', fontWeight: 600, color: '#0f172a', lineHeight: 1.5 }}>
                I understand that this is a clinical intake and screening aid, not a medical diagnosis, and I agree to proceed. <span style={{ color: '#dc2626' }}>*</span>
              </span>
            </label>

            <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', userSelect: 'none' }}>
              <input
                type="checkbox"
                checked={researchConsent}
                onChange={(e) => setResearchConsent(e.target.checked)}
                style={{ width: '19px', height: '19px', marginTop: '2px', accentColor: '#2563eb', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.84rem', color: '#64748b', lineHeight: 1.5 }}>
                (Optional) I consent to contributing my fully anonymized symptom data to headache research datasets to assist medical science.
              </span>
            </label>
          </div>

          {/* Start New Session Button */}
          <button
            onClick={() => onStartSession(researchConsent)}
            disabled={!agreed}
            style={{
              width: '100%',
              padding: '14px 20px',
              borderRadius: '12px',
              backgroundColor: agreed ? '#2563eb' : '#94a3b8',
              color: '#ffffff',
              fontSize: '1.02rem',
              fontWeight: 700,
              border: 'none',
              cursor: agreed ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              boxShadow: agreed ? '0 8px 20px -4px rgba(37, 99, 235, 0.4)' : 'none',
              transition: 'all 0.2s ease'
            }}
          >
            <span>Start Intake Interview</span>
            <ChevronRightIcon size={18} color="#ffffff" />
          </button>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', margin: '28px 0 20px 0' }}>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
            <span style={{ padding: '0 14px', fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
              or resume existing intake
            </span>
            <div style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }} />
          </div>

          {/* Resume Session Form */}
          <form onSubmit={handleResume} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Enter 6-character code (e.g. 9ELXEL)"
              value={resumeCode}
              onChange={(e) => setResumeCode(e.target.value.toUpperCase())}
              maxLength={6}
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '10px',
                border: '1.5px solid #cbd5e1',
                fontSize: '0.95rem',
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              style={{
                padding: '12px 20px',
                borderRadius: '10px',
                backgroundColor: '#0f172a',
                color: '#ffffff',
                border: 'none',
                fontWeight: 600,
                fontSize: '0.92rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              Resume Session
            </button>
          </form>

          {resumeError && (
            <p style={{ color: '#dc2626', fontSize: '0.84rem', marginTop: '8px', fontWeight: 500 }}>
              {resumeError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
