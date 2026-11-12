import React from 'react'
import { ShieldAlertIcon, PhoneCallIcon, AmbulanceIcon, DownloadIcon } from './Icons'

export default function RedFlagModal({ sessionCode, redFlagMessage, onDownloadReport }) {
  // Parse message text to remove raw markdown asterisks if present
  const cleanMessage = (redFlagMessage || '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/⚠️/g, '')

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '16px'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '20px',
        maxWidth: '560px',
        width: '100%',
        padding: '32px',
        boxShadow: '0 25px 50px -12px rgba(220, 38, 38, 0.35)',
        border: '3px solid #ef4444',
        position: 'relative'
      }}>
        {/* Header with Shield Alert SVG */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '20px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '14px',
            backgroundColor: '#fee2e2',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            border: '1px solid #fca5a5'
          }}>
            <ShieldAlertIcon size={30} color="#dc2626" />
          </div>
          <div>
            <span style={{
              display: 'inline-block',
              fontSize: '0.74rem',
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#991b1b',
              backgroundColor: '#fee2e2',
              padding: '3px 10px',
              borderRadius: '9999px',
              border: '1px solid #f87171'
            }}>
              Urgent Medical Attention Recommended
            </span>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#991b1b', marginTop: '6px', margin: 0, lineHeight: 1.3 }}>
              Please Seek Emergency Care Now
            </h2>
          </div>
        </div>

        {/* Clinical Warning Body */}
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          padding: '18px',
          borderRadius: '12px',
          marginBottom: '24px',
          color: '#7f1d1d',
          fontSize: '0.94rem',
          lineHeight: '1.6'
        }}>
          <p style={{ fontWeight: 700, marginBottom: '8px', color: '#991b1b' }}>
            A potential neurological or acute red-flag symptom was recorded:
          </p>
          <p style={{ whiteSpace: 'pre-wrap', marginBottom: '12px', color: '#450a0a' }}>
            {cleanMessage || 'Based on the symptom you described, prompt in-person medical evaluation is required.'}
          </p>
          <p style={{ fontSize: '0.86rem', color: '#991b1b', fontWeight: 600 }}>
            The intake interview has been safely locked. Do not wait for this questionnaire. Please go to the nearest hospital emergency department immediately.
          </p>
        </div>

        {/* Emergency Call Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
          <a
            href="tel:112"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              padding: '14px 18px',
              borderRadius: '12px',
              backgroundColor: '#dc2626',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '1.05rem',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(220, 38, 38, 0.4)',
              transition: 'transform 0.15s ease'
            }}
          >
            <PhoneCallIcon size={20} color="#ffffff" />
            <span>Call 112 (Emergency)</span>
          </a>

          <a
            href="tel:108"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              padding: '14px 18px',
              borderRadius: '12px',
              backgroundColor: '#991b1b',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '1.05rem',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(153, 27, 27, 0.4)',
              transition: 'transform 0.15s ease'
            }}
          >
            <AmbulanceIcon size={20} color="#ffffff" />
            <span>Call 108 (Ambulance)</span>
          </a>
        </div>

        {/* Download Urgent PDF */}
        <button
          onClick={onDownloadReport}
          style={{
            width: '100%',
            padding: '12px 18px',
            borderRadius: '10px',
            backgroundColor: '#ffffff',
            color: '#1e293b',
            border: '1.5px solid #cbd5e1',
            fontWeight: 600,
            fontSize: '0.92rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            transition: 'background-color 0.15s ease'
          }}
        >
          <DownloadIcon size={18} color="#1e293b" />
          <span>Download Urgent Clinical Summary for ER Physician</span>
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.82rem', color: '#64748b', marginTop: '16px' }}>
          Participant Reference Code: <strong style={{ color: '#0f172a', letterSpacing: '0.06em' }}>{sessionCode}</strong>
        </p>
      </div>
    </div>
  )
}
