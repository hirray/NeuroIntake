import React from 'react'

export default function RedFlagModal({ sessionCode, redFlagMessage, onDownloadReport }) {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      padding: '16px'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        maxWidth: '540px',
        width: '100%',
        padding: '28px',
        boxShadow: 'var(--shadow-lg)',
        border: '3px solid var(--urgent-red)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--urgent-red-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.8rem',
            color: 'var(--urgent-red)'
          }}>
            🚨
          </div>
          <div>
            <span className="badge badge-urgent">URGENT MEDICAL ATTENTION</span>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--urgent-red)', marginTop: '4px' }}>
              Please Seek Emergency Care Now
            </h2>
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--urgent-red-light)',
          padding: '16px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px',
          color: '#7f1d1d',
          fontSize: '0.95rem',
          lineHeight: '1.6'
        }}>
          <p style={{ fontWeight: 600, marginBottom: '8px' }}>
            Based on the symptoms you reported, immediate medical evaluation is required:
          </p>
          <p style={{ whiteSpace: 'pre-wrap', marginBottom: '12px' }}>
            {redFlagMessage || 'A dangerous neurological or acute red flag symptom was recorded.'}
          </p>
          <p style={{ fontSize: '0.9rem', fontStyle: 'italic' }}>
            The intake interview has been safely paused. Do not wait for this questionnaire or try to continue.
          </p>
        </div>

        {/* Emergency Call Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
          <a
            href="tel:112"
            className="btn btn-urgent"
            style={{ fontSize: '1.1rem', textDecoration: 'none' }}
          >
            📞 Call 112 (Emergency)
          </a>
          <a
            href="tel:108"
            className="btn btn-urgent"
            style={{ fontSize: '1.1rem', textDecoration: 'none', backgroundColor: '#991b1b' }}
          >
            🚑 Call 108 (Ambulance)
          </a>
        </div>

        {/* Download Urgent PDF */}
        <button
          className="btn btn-secondary"
          onClick={onDownloadReport}
          style={{ width: '100%', padding: '12px', fontWeight: 600 }}
        >
          📄 Download Urgent Clinical Summary for Emergency Doctor
        </button>

        <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '14px' }}>
          Participant Code: <b>{sessionCode}</b> (Keep this code for your hospital records)
        </p>
      </div>
    </div>
  )
}
