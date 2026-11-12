import React, { useState, useEffect, useRef } from 'react'

export default function ClinicianPortal({ onClose }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState('doctor')
  const [password, setPassword] = useState('clinical123')
  const [loginError, setLoginError] = useState('')

  const [sessions, setSessions] = useState([])
  const [filter, setFilter] = useState('all')
  const [selectedSessionId, setSelectedSessionId] = useState(null)
  const [sessionDetail, setSessionDetail] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  // Review Form
  const [decision, setDecision] = useState('Confirmed')
  const [doctorName, setDoctorName] = useState('Dr. R. Sharma, MD')
  const [regNumber, setRegNumber] = useState('MCI-489201')
  const [notes, setNotes] = useState('')
  const [confirmedType, setConfirmedType] = useState('Migraine without aura')
  const [reviewSaved, setReviewSaved] = useState(false)

  const detailPanelRef = useRef(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    try {
      const res = await fetch('/api/clinician/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      if (!res.ok) throw new Error('Invalid credentials')
      setIsLoggedIn(true)
      fetchSessions()
    } catch (err) {
      setLoginError('Invalid username or password. (Demo: doctor / clinical123)')
    }
  }

  const fetchSessions = async () => {
    try {
      const url = filter === 'all' ? '/api/clinician/sessions' : `/api/clinician/sessions?status=${filter}`
      const res = await fetch(url)
      const data = await res.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.error('Failed fetching sessions:', err)
    }
  }

  useEffect(() => {
    if (isLoggedIn) fetchSessions()
  }, [filter, isLoggedIn])

  const openSessionDetail = async (sid) => {
    setSelectedSessionId(sid)
    setIsLoadingDetail(true)
    setReviewSaved(false)
    try {
      const res = await fetch(`/api/clinician/session/${sid}`)
      const data = await res.json()
      setSessionDetail(data)
      if (data.review) {
        setDecision(data.review.decision || 'Confirmed')
        setDoctorName(data.review.doctor_name || '')
        setRegNumber(data.review.reg_number || '')
        setNotes(data.review.notes || '')
        setConfirmedType(data.review.confirmed_type || 'Migraine without aura')
      }
      // Scroll detail panel to top
      setTimeout(() => {
        detailPanelRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
      }, 100)
    } catch (err) {
      console.error('Error fetching session detail:', err)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const handleSaveReview = async (e) => {
    e.preventDefault()
    if (!selectedSessionId) return
    try {
      const res = await fetch('/api/clinician/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: selectedSessionId,
          decision,
          doctor_name: doctorName,
          reg_number: regNumber,
          notes,
          confirmed_type: confirmedType
        })
      })
      if (res.ok) {
        setReviewSaved(true)
        fetchSessions()
        openSessionDetail(selectedSessionId)
      }
    } catch (err) {
      console.error('Failed saving review:', err)
    }
  }

  const downloadReport = (sid) => {
    window.open(`/api/report/pdf/${sid}`, '_blank')
  }

  const downloadKaggleCSV = () => {
    window.open('/api/clinician/export/kaggle-csv', '_blank')
  }

  if (!isLoggedIn) {
    return (
      <div style={{ maxWidth: '440px', margin: '60px auto', padding: '24px' }}>
        <div style={{
          backgroundColor: '#ffffff',
          padding: '28px',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>
              🩺 Clinician Portal Login
            </h2>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem' }}>
              ✕
            </button>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Physician access for patient intake review, diagnosis verification, and research export.
          </p>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
                Doctor Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="text-input"
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="text-input"
                style={{ width: '100%' }}
              />
            </div>

            {loginError && (
              <p style={{ color: 'var(--urgent-red)', fontSize: '0.85rem' }}>{loginError}</p>
            )}

            <button type="submit" className="btn btn-primary" style={{ marginTop: '8px' }}>
              Sign In to Clinician Portal
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* ── Top Bar ─────────────────────────────── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: '#ffffff',
        flexShrink: 0,
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)', margin: 0 }}>
            🩺 Treating Physician Dashboard
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
            Review patient intake questionnaires, record clinical decisions, and sign PDF reports.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={downloadKaggleCSV} title="Export consented patient answers matching Kaggle migraine schema">
            📊 Export Research CSV
          </button>
          <button className="btn btn-secondary" onClick={() => setIsLoggedIn(false)}>Sign Out</button>
          <button className="btn btn-secondary" onClick={onClose}>Back to Patient Chat</button>
        </div>
      </div>

      {/* ── Main Body: Split Panel ───────────────── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* ── LEFT: Sessions List ─────────────── */}
        <div style={{
          width: selectedSessionId ? '42%' : '100%',
          display: 'flex',
          flexDirection: 'column',
          borderRight: selectedSessionId ? '2px solid var(--border-subtle)' : 'none',
          overflow: 'hidden',
          transition: 'width 0.25s ease'
        }}>
          {/* Filter Controls */}
          <div style={{ display: 'flex', gap: '6px', padding: '10px 14px', overflowX: 'auto', flexShrink: 0, borderBottom: '1px solid var(--border-subtle)', backgroundColor: '#f8fafc' }}>
            {[
              { id: 'all', label: 'All Cases' },
              { id: 'in_progress', label: 'In Progress' },
              { id: 'completed', label: 'Awaiting Review' },
              { id: 'urgent_red_flag', label: '🚨 Urgent' },
              { id: 'reviewed', label: '✅ Reviewed' }
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--border-strong)',
                  backgroundColor: filter === f.id ? 'var(--primary)' : '#ffffff',
                  color: filter === f.id ? '#ffffff' : 'var(--text-main)',
                  fontWeight: 600,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Sessions Table */}
          <div style={{ overflowY: 'auto', flex: 1 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0, zIndex: 1 }}>
                <tr>
                  <th style={{ padding: '9px 12px' }}>Code</th>
                  <th style={{ padding: '9px 12px' }}>Lang</th>
                  <th style={{ padding: '9px 12px' }}>Status</th>
                  <th style={{ padding: '9px 12px' }}>Consent</th>
                  <th style={{ padding: '9px 12px' }}>Review</th>
                  <th style={{ padding: '9px 12px' }}>Created</th>
                  <th style={{ padding: '9px 12px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => {
                  const isActive = s.session_id === selectedSessionId
                  return (
                    <tr
                      key={s.session_id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isActive ? '#eff6ff' : s.is_urgent ? 'var(--urgent-red-light)' : 'transparent',
                        cursor: 'default'
                      }}
                    >
                      <td style={{ padding: '9px 12px', fontWeight: 700 }}>{s.session_id}</td>
                      <td style={{ padding: '9px 12px', textTransform: 'uppercase', fontSize: '0.78rem' }}>{s.language}</td>
                      <td style={{ padding: '9px 12px' }}>
                        {s.is_urgent ? (
                          <span className="badge badge-urgent" style={{ fontSize: '0.72rem' }}>URGENT</span>
                        ) : (
                          <span className="badge" style={{ backgroundColor: '#e2e8f0', color: '#334155', fontSize: '0.72rem' }}>
                            {s.status.replace('_', ' ')}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '9px 12px', fontSize: '0.78rem' }}>{s.research_consent ? '✅' : '—'}</td>
                      <td style={{ padding: '9px 12px' }}>
                        {s.has_review ? (
                          <span className="badge badge-reviewed" style={{ fontSize: '0.72rem' }}>{s.review_decision || 'Reviewed'}</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Pending</span>
                        )}
                      </td>
                      <td style={{ padding: '9px 12px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                        {s.created_at ? s.created_at.slice(0, 16).replace('T', ' ') : '—'}
                      </td>
                      <td style={{ padding: '9px 12px', textAlign: 'right' }}>
                        <button
                          className="btn btn-primary"
                          onClick={() => openSessionDetail(s.session_id)}
                          style={{ padding: '4px 10px', fontSize: '0.78rem', minHeight: '30px', backgroundColor: isActive ? '#1d4ed8' : undefined }}
                        >
                          {isActive ? 'Viewing →' : 'Review Case →'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
                {sessions.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No sessions found under this filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── RIGHT: Case Detail Panel ───────────── */}
        {selectedSessionId && (
          <div
            ref={detailPanelRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              backgroundColor: '#f8fafc',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {/* Detail Panel Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 18px',
              backgroundColor: '#ffffff',
              borderBottom: '2px solid var(--primary)',
              position: 'sticky',
              top: 0,
              zIndex: 2,
              flexShrink: 0
            }}>
              <div>
                <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--primary)', margin: 0 }}>
                  Case File: #{selectedSessionId}
                </h2>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                  Clinical assessment &amp; physician review
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => downloadReport(selectedSessionId)}
                  style={{ fontSize: '0.8rem', padding: '5px 10px' }}
                >
                  📄 Print PDF
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setSelectedSessionId(null)}
                  style={{ fontSize: '0.8rem', padding: '5px 10px' }}
                >
                  ✕ Close
                </button>
              </div>
            </div>

            {/* Detail Content */}
            <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {isLoadingDetail ? (
                <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <p style={{ fontSize: '0.95rem' }}>⏳ Loading clinical assessment data...</p>
                </div>
              ) : sessionDetail ? (
                <>
                  {/* 1. Screening Result */}
                  <div style={{
                    backgroundColor: sessionDetail.screening?.is_urgent ? 'var(--urgent-red-light)' : '#ffffff',
                    border: `1.5px solid ${sessionDetail.screening?.is_urgent ? 'var(--urgent-red)' : 'var(--border-subtle)'}`,
                    padding: '14px 16px',
                    borderRadius: 'var(--radius-md)'
                  }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                      Automated ICHD-3 Screening Output (Clinician Aid — Not a Diagnosis)
                    </span>
                    <h3 style={{
                      fontSize: '1.05rem',
                      fontWeight: 700,
                      color: sessionDetail.screening?.is_urgent ? 'var(--urgent-red)' : 'var(--primary)',
                      margin: '6px 0 4px'
                    }}>
                      {sessionDetail.screening?.outcome?.replace(/_/g, ' ')}
                    </h3>
                    <p style={{ fontSize: '0.88rem', margin: '0 0 8px' }}>
                      {sessionDetail.screening?.summary_text}
                    </p>
                    {sessionDetail.screening?.specialist_flags?.length > 0 && (
                      <div style={{ color: '#c2410c', fontSize: '0.83rem', marginTop: '6px' }}>
                        <b>Specialist Review Flags:</b>
                        <ul style={{ paddingLeft: '18px', margin: '4px 0 0' }}>
                          {sessionDetail.screening.specialist_flags.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {sessionDetail.screening?.points_to_clarify?.length > 0 && (
                      <div style={{ marginTop: '6px', fontSize: '0.82rem', color: '#475569' }}>
                        <b>Points to Clarify:</b> {sessionDetail.screening.points_to_clarify.join('; ')}
                      </div>
                    )}
                  </div>

                  {/* 2. ICHD-3 Criteria Table */}
                  <div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                      ICHD-3 Diagnostic Criteria Breakdown
                    </h4>
                    <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#1e3a8a', color: '#ffffff' }}>
                            <th style={{ padding: '8px 10px', textAlign: 'left' }}>Criterion</th>
                            <th style={{ padding: '8px 10px', textAlign: 'left' }}>Required</th>
                            <th style={{ padding: '8px 10px', textAlign: 'left' }}>Patient Reported</th>
                            <th style={{ padding: '8px 10px', textAlign: 'left' }}>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sessionDetail.screening?.criteria_table?.map((c, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: i % 2 === 0 ? '#ffffff' : '#f9fafb' }}>
                              <td style={{ padding: '7px 10px', fontWeight: 600 }}>{c.criterion}</td>
                              <td style={{ padding: '7px 10px' }}>{c.required}</td>
                              <td style={{ padding: '7px 10px' }}>{c.patient_answer}</td>
                              <td style={{ padding: '7px 10px', fontWeight: 700 }}>
                                {c.met === true ? (
                                  <span style={{ color: 'var(--success-green)' }}>✓ MET</span>
                                ) : c.met === false ? (
                                  <span style={{ color: 'var(--urgent-red)' }}>✗ NOT MET</span>
                                ) : (
                                  <span style={{ color: 'var(--warning-amber)' }}>? UNKNOWN</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 3. Physician Decision Form */}
                  <div style={{
                    backgroundColor: '#ffffff',
                    border: '1.5px solid #cbd5e1',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px'
                  }}>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '12px' }}>
                      ✍️ Physician Decision &amp; Digital Sign-off
                    </h4>

                    <form onSubmit={handleSaveReview} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                            Clinical Decision
                          </label>
                          <select
                            value={decision}
                            onChange={(e) => setDecision(e.target.value)}
                            className="text-input"
                            style={{ width: '100%' }}
                          >
                            <option value="Confirmed">Confirmed (agrees with screening)</option>
                            <option value="Modified">Modified (different headache type)</option>
                            <option value="Not agreed">Not agreed (secondary / non-migraine)</option>
                          </select>
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                            Confirmed Headache Type
                          </label>
                          <select
                            value={confirmedType}
                            onChange={(e) => setConfirmedType(e.target.value)}
                            className="text-input"
                            style={{ width: '100%' }}
                          >
                            <option value="Migraine without aura">Migraine without aura</option>
                            <option value="Migraine with typical aura">Migraine with typical aura</option>
                            <option value="Chronic migraine">Chronic migraine</option>
                            <option value="Tension-type headache">Tension-type headache</option>
                            <option value="Trigeminal autonomic cephalgia">Trigeminal autonomic cephalgia</option>
                            <option value="Secondary headache">Secondary headache</option>
                            <option value="Other">Other</option>
                          </select>
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                            Doctor's Full Name
                          </label>
                          <input
                            type="text"
                            value={doctorName}
                            onChange={(e) => setDoctorName(e.target.value)}
                            className="text-input"
                            style={{ width: '100%' }}
                            required
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                            Medical Registration No.
                          </label>
                          <input
                            type="text"
                            value={regNumber}
                            onChange={(e) => setRegNumber(e.target.value)}
                            className="text-input"
                            style={{ width: '100%' }}
                            required
                          />
                        </div>
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, marginBottom: '4px' }}>
                          Clinical Impression &amp; Investigation / Treatment Plan
                        </label>
                        <textarea
                          rows={3}
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          placeholder="e.g. Clinical history consistent with episodic migraine without aura. Advised sleep regularity, hydration, and acute oral triptan at headache onset."
                          className="text-input"
                          style={{ width: '100%', resize: 'vertical' }}
                        />
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button type="submit" className="btn btn-primary">
                          Sign &amp; Record Physician Decision
                        </button>
                        {reviewSaved && (
                          <span style={{ color: 'var(--success-green)', fontWeight: 600, fontSize: '0.88rem' }}>
                            ✅ Decision recorded! PDF updated to "REVIEWED".
                          </span>
                        )}
                      </div>
                    </form>
                  </div>

                  {/* 4. Questionnaire Transcript */}
                  <div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
                      Full Questionnaire Transcript
                    </h4>
                    <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.79rem' }}>
                        <thead style={{ backgroundColor: '#f8fafc' }}>
                          <tr>
                            <th style={{ padding: '6px 10px', textAlign: 'left' }}>ID</th>
                            <th style={{ padding: '6px 10px', textAlign: 'left' }}>Question Label</th>
                            <th style={{ padding: '6px 10px', textAlign: 'left' }}>Answer</th>
                            <th style={{ padding: '6px 10px', textAlign: 'left' }}>Patient Transcript / Translation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sessionDetail.questionnaire?.map((q) => (
                            <tr key={q.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                              <td style={{ padding: '6px 10px', fontWeight: 700 }}>{q.id}</td>
                              <td style={{ padding: '6px 10px' }}>{q.label}</td>
                              <td style={{ padding: '6px 10px', fontWeight: 600 }}>{String(q.value ?? '—')}</td>
                              <td style={{ padding: '6px 10px' }}>
                                {q.raw_text || '—'}
                                {q.translation && (
                                  <span style={{ color: 'var(--text-muted)', display: 'block', fontStyle: 'italic' }}>
                                    [Machine-translated]: {q.translation}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
