import React, { useState, useEffect } from 'react'

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
        // Refresh detail
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
    <div style={{ maxWidth: '1000px', margin: '20px auto', padding: '16px' }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--border-subtle)'
      }}>
        {/* Top Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--primary)' }}>
              🩺 Treating Physician Dashboard
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Review patient intake questionnaires, record clinical decisions, and sign PDF reports.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary" onClick={downloadKaggleCSV} title="Export consented patient answers matching Kaggle migraine schema">
              📊 Export Kaggle Research CSV
            </button>
            <button className="btn btn-secondary" onClick={() => setIsLoggedIn(false)}>
              Sign Out
            </button>
            <button className="btn btn-secondary" onClick={onClose}>
              Back to Patient Chat
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto', paddingBottom: '4px' }}>
          {[
            { id: 'all', label: 'All Cases' },
            { id: 'in_progress', label: 'In Progress' },
            { id: 'completed', label: 'Awaiting Review' },
            { id: 'urgent_red_flag', label: '🚨 Urgent Red Flags' },
            { id: 'reviewed', label: '✅ Reviewed' }
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border-strong)',
                backgroundColor: filter === f.id ? 'var(--primary)' : '#ffffff',
                color: filter === f.id ? '#ffffff' : 'var(--text-main)',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Sessions Table */}
        <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid var(--border-subtle)' }}>
              <tr>
                <th style={{ padding: '10px 14px' }}>Code</th>
                <th style={{ padding: '10px 14px' }}>Language</th>
                <th style={{ padding: '10px 14px' }}>Status</th>
                <th style={{ padding: '10px 14px' }}>Research Consent</th>
                <th style={{ padding: '10px 14px' }}>Doctor Review</th>
                <th style={{ padding: '10px 14px' }}>Created</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.session_id} style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: s.is_urgent ? 'var(--urgent-red-light)' : 'transparent' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700 }}>{s.session_id}</td>
                  <td style={{ padding: '10px 14px', textTransform: 'uppercase' }}>{s.language}</td>
                  <td style={{ padding: '10px 14px' }}>
                    {s.is_urgent ? (
                      <span className="badge badge-urgent">URGENT RED FLAG</span>
                    ) : (
                      <span className="badge" style={{ backgroundColor: '#e2e8f0', color: '#334155' }}>
                        {s.status.replace('_', ' ')}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px' }}>{s.research_consent ? '✅ Yes' : 'No'}</td>
                  <td style={{ padding: '10px 14px' }}>
                    {s.has_review ? (
                      <span className="badge badge-reviewed">{s.review_decision || 'Reviewed'}</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Pending</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {s.created_at ? s.created_at.slice(0, 16).replace('T', ' ') : '—'}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => openSessionDetail(s.session_id)}
                      style={{ padding: '4px 10px', fontSize: '0.8rem', minHeight: '32px' }}
                    >
                      Review Case →
                    </button>
                  </td>
                </tr>
              ))}
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

        {/* Selected Session Clinical Detail Modal / Drawer */}
        {selectedSessionId && (
          <div style={{
            marginTop: '28px',
            borderTop: '2px solid var(--primary)',
            paddingTop: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>
                Case File: Participant #{selectedSessionId}
              </h2>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => downloadReport(selectedSessionId)}
                >
                  📄 View / Print PDF Report
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setSelectedSessionId(null)}
                >
                  Close Case
                </button>
              </div>
            </div>

            {isLoadingDetail ? (
              <p>Loading clinical assessment data...</p>
            ) : sessionDetail ? (
              <div>
                {/* 1. Screening Result Box */}
                <div style={{
                  backgroundColor: sessionDetail.screening?.is_urgent ? 'var(--urgent-red-light)' : '#f8fafc',
                  border: `1.5px solid ${sessionDetail.screening?.is_urgent ? 'var(--urgent-red)' : 'var(--border-subtle)'}`,
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '16px'
                }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                    Automated ICHD-3 Screening Output (Draft Clinician Aid)
                  </span>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: sessionDetail.screening?.is_urgent ? 'var(--urgent-red)' : 'var(--primary)', marginTop: '4px' }}>
                    {sessionDetail.screening?.outcome?.replace(/_/g, ' ')}
                  </h3>
                  <p style={{ fontSize: '0.92rem', marginTop: '4px' }}>
                    {sessionDetail.screening?.summary_text}
                  </p>
                  {sessionDetail.screening?.specialist_flags?.length > 0 && (
                    <div style={{ marginTop: '8px', color: '#c2410c', fontSize: '0.88rem' }}>
                      <b>Specialist Review Flags:</b>
                      <ul style={{ paddingLeft: '20px' }}>
                        {sessionDetail.screening.specialist_flags.map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {sessionDetail.screening?.points_to_clarify?.length > 0 && (
                    <div style={{ marginTop: '8px', fontSize: '0.85rem', color: '#475569' }}>
                      <b>Points for Doctor to Clarify:</b> {sessionDetail.screening.points_to_clarify.join('; ')}
                    </div>
                  )}
                </div>

                {/* 2. Criteria Assessment Table */}
                <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
                  ICHD-3 Diagnostic Criteria Breakdown
                </h4>
                <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid var(--border-subtle)' }}>
                        <th style={{ padding: '8px 12px' }}>Criterion</th>
                        <th style={{ padding: '8px 12px' }}>Required Threshold</th>
                        <th style={{ padding: '8px 12px' }}>Patient Reported</th>
                        <th style={{ padding: '8px 12px' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessionDetail.screening?.criteria_table?.map((c, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '8px 12px', fontWeight: 600 }}>{c.criterion}</td>
                          <td style={{ padding: '8px 12px' }}>{c.required}</td>
                          <td style={{ padding: '8px 12px' }}>{c.patient_answer}</td>
                          <td style={{ padding: '8px 12px', fontWeight: 700 }}>
                            {c.met === true ? (
                              <span style={{ color: 'var(--success-green)' }}>MET</span>
                            ) : c.met === false ? (
                              <span style={{ color: 'var(--urgent-red)' }}>NOT MET</span>
                            ) : (
                              <span style={{ color: 'var(--warning-amber)' }}>UNKNOWN</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 3. Doctor Decision Form */}
                <div style={{
                  backgroundColor: '#f8fafc',
                  border: '1.5px solid #cbd5e1',
                  borderRadius: 'var(--radius-md)',
                  padding: '18px',
                  marginBottom: '20px'
                }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '12px' }}>
                    ✍️ Physician Decision & Digital Sign-off
                  </h4>

                  <form onSubmit={handleSaveReview} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
                          Clinical Decision
                        </label>
                        <select
                          value={decision}
                          onChange={(e) => setDecision(e.target.value)}
                          className="text-input"
                          style={{ width: '100%' }}
                        >
                          <option value="Confirmed">Confirmed (Agrees with screening)</option>
                          <option value="Modified">Modified (Different headache type)</option>
                          <option value="Not agreed">Not agreed (Secondary or non-migraine)</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
                          Confirmed Type (for research CSV)
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
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
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
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
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
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '4px' }}>
                        Clinical Impression & Investigation / Treatment Plan
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
                        Sign & Record Physician Decision
                      </button>
                      {reviewSaved && (
                        <span style={{ color: 'var(--success-green)', fontWeight: 600, fontSize: '0.9rem' }}>
                          ✅ Decision recorded! PDF updated to "REVIEWED".
                        </span>
                      )}
                    </div>
                  </form>
                </div>

                {/* 4. Complete Questionnaire Transcript Table */}
                <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
                  Full Questionnaire Transcript
                </h4>
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead style={{ backgroundColor: '#f8fafc' }}>
                      <tr>
                        <th style={{ padding: '6px 10px' }}>ID</th>
                        <th style={{ padding: '6px 10px' }}>Question Label</th>
                        <th style={{ padding: '6px 10px' }}>Coded Answer</th>
                        <th style={{ padding: '6px 10px' }}>Patient Raw Transcript / Translation</th>
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
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
