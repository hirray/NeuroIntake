import React, { useState, useEffect, useRef } from 'react'
import LanguageSelector, { LANGUAGES } from './LanguageSelector'
import {
  BrainIcon,
  ShieldAlertIcon,
  StethoscopeIcon,
  SpeakerIcon,
  SpeakerOffIcon,
  MicIcon,
  SendIcon,
  PlusIcon,
  HistoryIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  FileTextIcon,
  TrashIcon,
  ArrowLeftIcon,
  SkipForwardIcon,
  HelpCircleIcon,
  DownloadIcon,
  PhoneCallIcon,
  AmbulanceIcon,
  ActivityIcon,
  ClockIcon
} from './Icons'

// Questionnaire Stages mapping for the Left Sidebar Checklist
const QUESTION_STAGES = [
  { id: 'safety', label: 'Safety & Red Flags', prefix: 'E' },
  { id: 'profile', label: 'Patient Profile', prefix: 'P' },
  { id: 'headache', label: 'Headache Traits', prefix: 'H' },
  { id: 'aura', label: 'Aura & Neurology', prefix: 'A' },
  { id: 'history', label: 'History & Triggers', prefix: 'F' },
  { id: 'lifestyle', label: 'Lifestyle (Optional)', prefix: 'L' }
]

function getStageForQuestion(qid) {
  if (!qid) return 0
  const firstChar = qid.charAt(0).toUpperCase()
  if (firstChar === 'E') return 0
  if (firstChar === 'P') return 1
  if (firstChar === 'H') return 2
  if (firstChar === 'A') return 3
  if (firstChar === 'F') return 4
  if (firstChar === 'L') return 5
  return 2
}

export default function ChatView({
  sessionCode,
  language,
  onLanguageChange,
  initialBotMessage,
  initialChatHistory = [],
  initialAnswers = {},
  onResumeSession,
  onOpenClinician,
  onResetSession
}) {
  const [messages, setMessages] = useState([])
  const [answers, setAnswers] = useState(initialAnswers)
  const [currentBotMsg, setCurrentBotMsg] = useState(initialBotMessage)
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(true)
  const [speechErrorNotice, setSpeechErrorNotice] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [recentSessions, setRecentSessions] = useState([])
  const [copiedCode, setCopiedCode] = useState(false)

  // Default Auto-Read Aloud is ON as requested by user
  const [autoRead, setAutoRead] = useState(() => {
    return localStorage.getItem('migraine_auto_read') !== 'false'
  })
  const [isSpeaking, setIsSpeaking] = useState(false)

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const lastSpokenTextRef = useRef('')
  const autoReadRef = useRef(autoRead)
  autoReadRef.current = autoRead

  // Fetch recent sessions for ChatGPT-style left sidebar
  const fetchRecentSessions = async () => {
    try {
      const res = await fetch('/api/session/recent/list')
      if (res.ok) {
        const data = await res.json()
        setRecentSessions(data.sessions || [])
      }
    } catch (err) {
      console.warn('Failed to load recent sessions:', err)
    }
  }

  useEffect(() => {
    fetchRecentSessions()
  }, [sessionCode])

  // Initialize and reconstruct chat history stream
  useEffect(() => {
    const combined = []
    if (initialChatHistory && initialChatHistory.length > 0) {
      combined.push(...initialChatHistory)
    }

    if (initialBotMessage) {
      setCurrentBotMsg(initialBotMessage)
      setProgress(initialBotMessage.progress_percentage || 0)

      // Only append bot message if not already present at the end
      const lastMsg = combined[combined.length - 1]
      if (!lastMsg || lastMsg.sender !== 'bot' || lastMsg.text !== initialBotMessage.text) {
        combined.push({
          sender: 'bot',
          text: initialBotMessage.text,
          question_id: initialBotMessage.question_id,
          question_type: initialBotMessage.question_type,
          options: initialBotMessage.options,
          is_red_flag_alert: initialBotMessage.is_red_flag_alert
        })
      }
    }
    setMessages(combined)
    setAnswers(initialAnswers)
  }, [initialBotMessage, initialChatHistory, initialAnswers])

  // Initialize Speech Recognition (Speech-to-Text)
  useEffect(() => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRec) {
      setSpeechSupported(false)
      return
    }

    const rec = new SpeechRec()
    rec.continuous = false
    rec.interimResults = false

    const langObj = LANGUAGES.find(l => l.code === language) || LANGUAGES[0]
    rec.lang = langObj.speechCode

    rec.onstart = () => setIsListening(true)
    rec.onend = () => setIsListening(false)

    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInputText(transcript)
      handleSendMessage(transcript, 'voice')
    }

    rec.onerror = () => {
      setIsListening(false)
      setSpeechErrorNotice('Microphone audio not captured. Please type or tap option buttons.')
      setTimeout(() => setSpeechErrorNotice(''), 4000)
    }

    recognitionRef.current = rec
  }, [language])

  // Auto-scroll to bottom on message stream changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Text-to-Speech (TTS) Core Handler
  const speakText = (text) => {
    if (!('speechSynthesis' in window) || !text) return
    window.speechSynthesis.cancel()

    // Clean text: strip markdown syntax, formatting asterisks, and emojis
    const cleanSpeech = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/[#*_~`]/g, '')
      .replace(/⚠️|🚨|📋|🩺|🧠|🎙️|🔊/g, '')
      .trim()

    if (!cleanSpeech) return

    const utterance = new SpeechSynthesisUtterance(cleanSpeech)
    const langObj = LANGUAGES.find(l => l.code === language) || LANGUAGES[0]
    utterance.lang = langObj.speechCode

    const voices = window.speechSynthesis.getVoices()
    const matchingVoice = voices.find(v => v.lang.startsWith(language) || v.lang === langObj.speechCode)
    if (matchingVoice) utterance.voice = matchingVoice

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    setIsSpeaking(false)
  }

  // Auto-Read Aloud Toggle Handler
  const toggleAutoRead = () => {
    if (autoRead) {
      stopSpeaking()
      setAutoRead(false)
      localStorage.setItem('migraine_auto_read', 'false')
    } else {
      setAutoRead(true)
      localStorage.setItem('migraine_auto_read', 'true')
      if (currentBotMsg?.text) {
        speakText(currentBotMsg.text)
      }
    }
  }

  // Automatic Read Aloud effect: speaks every incoming bot question by default unless muted
  useEffect(() => {
    if (autoRead && currentBotMsg?.text && currentBotMsg.text !== lastSpokenTextRef.current) {
      lastSpokenTextRef.current = currentBotMsg.text
      const timer = setTimeout(() => {
        speakText(currentBotMsg.text)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [currentBotMsg?.text, autoRead, language])

  // Stop speaking when component unmounts
  useEffect(() => {
    return () => {
      stopSpeaking()
    }
  }, [])

  const toggleMic = () => {
    if (!speechSupported) {
      setSpeechErrorNotice('Speech recognition not supported in this browser. Please type.')
      return
    }
    if (isListening) {
      recognitionRef.current?.stop()
    } else {
      setSpeechErrorNotice('')
      // If AI is currently speaking, stop it so mic doesn't pick it up
      stopSpeaking()
      try {
        recognitionRef.current?.start()
      } catch (err) {
        console.warn('Speech start error:', err)
      }
    }
  }

  const copySessionCode = () => {
    if (sessionCode) {
      navigator.clipboard.writeText(sessionCode)
      setCopiedCode(true)
      setTimeout(() => setCopiedCode(false), 2000)
    }
  }

  const handleSendMessage = async (text, inputMode = 'type', selectedCode = null) => {
    if (!text && selectedCode === null) return
    setIsLoading(true)

    // Stop ongoing speech when user submits an answer
    stopSpeaking()

    // Append user message immediately
    const userDisplay = selectedCode !== null
      ? (selectedCode === 'yes' ? 'Yes' : selectedCode === 'no' ? 'No' : String(selectedCode))
      : text

    const userEntry = { sender: 'user', text: userDisplay, input_mode: inputMode }
    setMessages(prev => [...prev, userEntry])
    setInputText('')

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionCode,
          message: text || userDisplay,
          input_mode: inputMode,
          selected_code: selectedCode
        })
      })

      if (!res.ok) throw new Error('Failed to send message')
      const data = await res.json()

      // Update bot message & progress
      const botMsg = data.bot_message
      setCurrentBotMsg(botMsg)
      setProgress(botMsg.progress_percentage || progress)

      // Update answers dictionary
      if (data.answers) {
        setAnswers(data.answers)
      }

      // Append bot message to stream
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: botMsg.text,
          question_id: botMsg.question_id,
          question_type: botMsg.question_type,
          options: botMsg.options,
          is_red_flag_alert: botMsg.is_red_flag_alert
        }
      ])

      // Refresh sidebar list
      fetchRecentSessions()

      // Automatically read aloud incoming response if autoRead is ON
      if (autoReadRef.current && botMsg?.text) {
        speakText(botMsg.text)
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: 'We encountered an error saving your response. Please try tapping or typing again.',
          is_error: true
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSpecialAction = (command) => {
    handleSendMessage(command, 'command')
  }

  const handleDeleteData = async () => {
    if (!window.confirm('Are you sure you want to delete all answers and end this session?')) return
    try {
      await fetch('/api/privacy/delete-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionCode })
      })
      alert('Your intake session and answers have been securely wiped.')
      onResetSession()
    } catch (err) {
      alert('Failed to delete session data.')
    }
  }

  // Parse markdown bold **text** into styled React elements
  const formatMarkdownText = (rawText) => {
    if (!rawText) return ''
    const parts = rawText.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} style={{ color: '#0f172a', fontWeight: 700 }}>
            {part.slice(2, -2)}
          </strong>
        )
      }
      return <span key={idx}>{part}</span>
    })
  }

  // Determine current active stage index
  const currentStageIndex = getStageForQuestion(currentBotMsg?.question_id)
  const isRedFlagActive = currentBotMsg?.is_red_flag_alert || messages.some(m => m.is_red_flag_alert)

  // Clinical Summary Helpers from answers
  const ageVal = answers['D1'] || '—'
  const durationVal = answers['H2'] ? `${answers['H2']} hrs` : '—'
  const freqVal = answers['H1'] || answers['D2'] || '—'
  const locationVal = answers['H3'] || '—'
  const throbbingVal = answers['H4'] ? 'Yes' : '—'

  // Criteria metrics tally
  const critCMet = [
    answers['H3'] === 'unilateral',
    answers['H4'] === true,
    answers['H5'] === 'moderate' || answers['H5'] === 'severe',
    answers['H6'] === true
  ].filter(Boolean).length

  const critDMet = [
    answers['A1'] === true,
    answers['A2'] === true || answers['A3'] === true
  ].filter(Boolean).length

  return (
    <div className="app-container">
      {/* 1. LEFT SIDEBAR (ChatGPT Style) */}
      <aside className="sidebar-left">
        {/* Brand Header */}
        <div className="sidebar-header">
          <div className="sidebar-brand-icon">
            <BrainIcon size={22} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
              MigraineAssist
            </h2>
            <p style={{ fontSize: '0.74rem', color: '#94a3b8', margin: 0 }}>
              ICHD-3 Clinical Intake
            </p>
          </div>
        </div>

        {/* Content Area */}
        <div className="sidebar-content">
          {/* New Intake Session Button */}
          <button
            className="btn-new-chat"
            onClick={onResetSession}
            title="Start a fresh clinical interview"
          >
            <PlusIcon size={18} color="#60a5fa" />
            <span>New Intake Session</span>
          </button>

          {/* Questionnaire Stage Navigator */}
          <div>
            <p className="sidebar-section-title">Clinical Protocol Stages</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {QUESTION_STAGES.map((stage, idx) => {
                const isActive = idx === currentStageIndex
                const isDone = idx < currentStageIndex
                return (
                  <div
                    key={stage.id}
                    className={`stage-step ${isActive ? 'active' : ''} ${isDone ? 'completed' : ''}`}
                  >
                    <div className="step-indicator">
                      {isDone ? <CheckCircleIcon size={14} color="#ffffff" /> : idx + 1}
                    </div>
                    <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {stage.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Recent Sessions List */}
          <div>
            <p className="sidebar-section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <HistoryIcon size={14} color="#94a3b8" />
              <span>Recent Sessions</span>
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {recentSessions.length === 0 ? (
                <p style={{ fontSize: '0.78rem', color: '#64748b', padding: '6px 10px' }}>
                  No past sessions recorded yet
                </p>
              ) : (
                recentSessions.slice(0, 8).map((s) => {
                  const isCurrent = s.session_id === sessionCode
                  return (
                    <div
                      key={s.session_id}
                      className={`history-item ${isCurrent ? 'active' : ''}`}
                      onClick={() => onResumeSession(s.session_id)}
                      title={`Resume session ${s.session_id}`}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, letterSpacing: '0.04em' }}>
                          {s.session_id}
                        </span>
                        {s.is_urgent && (
                          <span style={{
                            fontSize: '0.68rem',
                            backgroundColor: '#ef4444',
                            color: '#ffffff',
                            padding: '1px 6px',
                            borderRadius: '4px',
                            fontWeight: 700
                          }}>
                            URGENT
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                        {s.language.toUpperCase()}
                      </span>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer with Language and Doctor Login */}
        <div className="sidebar-footer">
          <LanguageSelector
            currentLang={language}
            onLanguageChange={onLanguageChange}
            dark={true}
          />
          <button
            onClick={onOpenClinician}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '9px 14px',
              borderRadius: '8px',
              backgroundColor: '#1e293b',
              color: '#38bdf8',
              border: '1px solid #334155',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background-color 0.15s ease'
            }}
          >
            <StethoscopeIcon size={16} color="#38bdf8" />
            <span>Doctor / Clinician Portal</span>
          </button>
        </div>
      </aside>

      {/* 2. CENTER CHAT AREA */}
      <main className="main-chat-area">
        {/* Top Floating App Bar */}
        <header className="chat-header">
          {/* Session Code Chip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>
              Session Code:
            </span>
            <button
              onClick={copySessionCode}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '8px',
                backgroundColor: '#eff6ff',
                color: '#1d4ed8',
                border: '1px solid #bfdbfe',
                fontSize: '0.86rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                cursor: 'pointer'
              }}
              title="Click to copy session code"
            >
              <span>{sessionCode || '—'}</span>
              <span style={{ fontSize: '0.72rem', color: '#3b82f6' }}>
                {copiedCode ? '✓ Copied' : 'Copy'}
              </span>
            </button>
          </div>

          {/* Progress Bar in Header */}
          <div style={{ flex: 1, maxWidth: '320px', margin: '0 24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ flex: 1, height: '8px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${progress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #2563eb, #059669)',
                  transition: 'width 0.4s ease'
                }}
              />
            </div>
            <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, minWidth: '32px' }}>
              {progress}%
            </span>
          </div>

          {/* Actions: Auto-Read Aloud Toggle and PDF Report */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* Auto-Read Aloud Toggle Button (Default ON) */}
            <button
              onClick={toggleAutoRead}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 14px',
                borderRadius: '9999px',
                border: autoRead ? '1.5px solid #3b82f6' : '1.5px solid #cbd5e1',
                backgroundColor: autoRead ? (isSpeaking ? '#dbeafe' : '#eff6ff') : '#ffffff',
                color: autoRead ? '#1d4ed8' : '#64748b',
                fontSize: '0.84rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isSpeaking ? '0 0 10px rgba(37, 99, 235, 0.3)' : 'none'
              }}
              title={autoRead ? 'Voice auto-read is ON. Click to stop and mute.' : 'Voice auto-read is OFF. Click to turn on.'}
              aria-label="Toggle automatic text-to-speech"
            >
              {autoRead ? (
                <>
                  <SpeakerIcon size={16} color="#2563eb" />
                  <span>{isSpeaking ? 'Speaking...' : 'Auto-Read: ON'}</span>
                </>
              ) : (
                <>
                  <SpeakerOffIcon size={16} color="#64748b" />
                  <span>Auto-Read: OFF</span>
                </>
              )}
            </button>

            <a
              href={`/api/report/pdf/${sessionCode}`}
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '8px',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                textDecoration: 'none',
                fontSize: '0.84rem',
                fontWeight: 600
              }}
              title="Download Draft Clinical Summary PDF"
            >
              <DownloadIcon size={16} color="#ffffff" />
              <span>PDF Report</span>
            </a>
          </div>
        </header>

        {/* Scrollable Chat Feed */}
        <div className="chat-messages-container">
          <div className="chat-messages-inner">
            {/* Render all historical and current messages */}
            {messages.map((msg, index) => {
              if (msg.sender === 'user') {
                return (
                  <div key={index} className="user-message-row">
                    <div className="user-bubble">
                      <p style={{ margin: 0 }}>{msg.text}</p>
                    </div>
                  </div>
                )
              }

              // Bot message card
              const isUrgent = msg.is_red_flag_alert || msg.text?.includes('URGENT MEDICAL ATTENTION')
              const isLastBotMessage = index === messages.length - 1 || (index === messages.length - 2 && messages[messages.length - 1].sender === 'user')

              return (
                <div key={index} className="bot-message-row">
                  <div className="bot-avatar" style={{ background: isUrgent ? '#ef4444' : undefined }}>
                    {isUrgent ? (
                      <ShieldAlertIcon size={20} color="#ffffff" />
                    ) : (
                      <BrainIcon size={20} color="#ffffff" />
                    )}
                  </div>

                  <div className={`bot-card ${isUrgent ? 'urgent' : ''}`}>
                    {/* Header with badge and optional replay button */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      {isUrgent ? (
                        <span className="badge badge-urgent">
                          <ShieldAlertIcon size={14} color="#dc2626" />
                          Urgent Safety Alert
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600 }}>
                          MigraineAssist AI
                        </span>
                      )}

                      {/* Manual Replay Audio Button */}
                      <button
                        onClick={() => speakText(msg.text)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: '#64748b',
                          fontSize: '0.74rem',
                          padding: '2px 6px',
                          borderRadius: '4px'
                        }}
                        title="Replay audio aloud"
                      >
                        <SpeakerIcon size={13} color="#64748b" />
                        <span>Listen</span>
                      </button>
                    </div>

                    {/* Bot Message Text with Markdown formatting */}
                    <div className="bot-card-text" style={{ whiteSpace: 'pre-wrap' }}>
                      {formatMarkdownText(msg.text)}
                    </div>

                    {/* If Urgent: Provide Emergency Call Buttons */}
                    {isUrgent && (
                      <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
                        <a
                          href="tel:112"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '10px 18px',
                            borderRadius: '10px',
                            backgroundColor: '#dc2626',
                            color: '#ffffff',
                            fontWeight: 700,
                            fontSize: '0.94rem',
                            textDecoration: 'none',
                            boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)'
                          }}
                        >
                          <PhoneCallIcon size={18} color="#ffffff" />
                          <span>Call 112 (National Emergency)</span>
                        </a>

                        <a
                          href="tel:108"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '10px 18px',
                            borderRadius: '10px',
                            backgroundColor: '#991b1b',
                            color: '#ffffff',
                            fontWeight: 700,
                            fontSize: '0.94rem',
                            textDecoration: 'none',
                            boxShadow: '0 4px 12px rgba(153, 27, 27, 0.3)'
                          }}
                        >
                          <AmbulanceIcon size={18} color="#ffffff" />
                          <span>Call 108 (Ambulance)</span>
                        </a>
                      </div>
                    )}

                    {/* Interactive Option Pills for the current active question */}
                    {isLastBotMessage && !isUrgent && msg.options && msg.options.length > 0 && (
                      <div className="options-grid">
                        {msg.options.map((opt) => (
                          <button
                            key={opt.code}
                            className="option-btn"
                            disabled={isLoading}
                            onClick={() => handleSendMessage(opt.label, 'button', opt.code)}
                          >
                            <span>{opt.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="bot-message-row">
                <div className="bot-avatar">
                  <BrainIcon size={20} color="#ffffff" />
                </div>
                <div className="bot-card" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#2563eb', animation: 'bounce 1s infinite 0.1s' }} />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#2563eb', animation: 'bounce 1s infinite 0.2s' }} />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#2563eb', animation: 'bounce 1s infinite 0.3s' }} />
                  </div>
                  <span style={{ fontSize: '0.86rem', color: '#64748b' }}>Processing response and checking safety rules...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Floating Input Capsule at Bottom */}
        <div className="chat-bottom-wrapper">
          {speechErrorNotice && (
            <p style={{ fontSize: '0.82rem', color: '#dc2626', marginBottom: '8px', fontWeight: 500 }}>
              {speechErrorNotice}
            </p>
          )}

          <div className="chat-input-capsule">
            {/* Microphone Button */}
            <button
              className={`mic-btn ${isListening ? 'active' : ''}`}
              onClick={toggleMic}
              type="button"
              title={isListening ? 'Listening... click to stop' : 'Click to speak your answer'}
              aria-label="Voice input"
            >
              <MicIcon size={20} color={isListening ? '#ffffff' : '#2563eb'} />
            </button>

            {/* Main Text Input */}
            <input
              type="text"
              className="chat-text-input"
              placeholder={isListening ? 'Listening to your voice...' : 'Type your answer or speak naturally...'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage(inputText, 'type')
                }
              }}
              disabled={isLoading || isRedFlagActive}
            />

            {/* Send Button */}
            <button
              className="send-btn"
              onClick={() => handleSendMessage(inputText, 'type')}
              disabled={!inputText.trim() || isLoading || isRedFlagActive}
              type="button"
              aria-label="Send message"
            >
              <SendIcon size={18} color="#ffffff" />
            </button>
          </div>

          {/* Quick Action Navigation Buttons */}
          <div className="action-toolbar">
            <button
              className="action-link-btn"
              onClick={() => handleSpecialAction('back')}
              disabled={isLoading || isRedFlagActive}
              title="Revise your previous answer"
            >
              <ArrowLeftIcon size={14} />
              <span>Go Back</span>
            </button>

            <button
              className="action-link-btn"
              onClick={() => handleSpecialAction('skip')}
              disabled={isLoading || isRedFlagActive}
              title="Skip this question"
            >
              <SkipForwardIcon size={14} />
              <span>Skip</span>
            </button>

            <button
              className="action-link-btn"
              onClick={() => handleSpecialAction('unknown')}
              disabled={isLoading || isRedFlagActive}
              title="Mark as not sure"
            >
              <HelpCircleIcon size={14} />
              <span>I Don't Know</span>
            </button>

            <a
              href={`/api/report/pdf/${sessionCode}`}
              target="_blank"
              rel="noreferrer"
              className="action-link-btn"
              title="Download your full answer transcript as PDF"
            >
              <DownloadIcon size={14} />
              <span>Download PDF</span>
            </a>

            <button
              className="action-link-btn danger"
              onClick={handleDeleteData}
              title="Erase all intake data"
            >
              <TrashIcon size={14} />
              <span>Delete Data</span>
            </button>
          </div>
        </div>
      </main>

      {/* 3. RIGHT SIDEBAR (Live Clinical Summary & ICHD-3 Engine) */}
      <aside className="sidebar-right">
        <div className="sidebar-right-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ActivityIcon size={18} color="#2563eb" />
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Clinical Summary
            </h3>
          </div>
          <span className={`badge ${isRedFlagActive ? 'badge-urgent' : 'badge-info'}`}>
            {isRedFlagActive ? 'Red Flag' : 'Live Intake'}
          </span>
        </div>

        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Urgent Alert Banner if Red Flag */}
          {isRedFlagActive && (
            <div style={{
              backgroundColor: '#fef2f2',
              border: '2px solid #ef4444',
              borderRadius: '12px',
              padding: '14px',
              color: '#991b1b'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.9rem', marginBottom: '6px' }}>
                <ShieldAlertIcon size={18} color="#dc2626" />
                <span>Emergency Flag Active</span>
              </div>
              <p style={{ fontSize: '0.82rem', lineHeight: 1.5, margin: 0 }}>
                A dangerous symptom was flagged. Please contact emergency services right away.
              </p>
            </div>
          )}

          {/* Patient Profile Card */}
          <div className="clinical-card">
            <h4 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', marginBottom: '10px' }}>
              Patient Intake Profile
            </h4>
            <div className="metric-row">
              <span className="metric-label">Age</span>
              <span className="metric-value">{ageVal}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Attack Duration</span>
              <span className="metric-value">{durationVal}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Attack Frequency</span>
              <span className="metric-value">{freqVal}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Pain Location</span>
              <span className="metric-value" style={{ textTransform: 'capitalize' }}>{locationVal}</span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Pulsating / Throbbing</span>
              <span className="metric-value">{throbbingVal}</span>
            </div>
          </div>

          {/* Real-time ICHD-3 Diagnostic Watchlist */}
          <div className="clinical-card">
            <h4 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', marginBottom: '10px' }}>
              ICHD-3 Criteria Tracker
            </h4>

            {/* Criterion A */}
            <div className={`criteria-item ${answers['H1'] || answers['D2'] ? 'met' : ''}`}>
              <CheckCircleIcon size={16} color={answers['H1'] || answers['D2'] ? '#059669' : '#94a3b8'} />
              <div>
                <p style={{ fontWeight: 600, margin: 0 }}>Criterion A: ≥ 5 Attacks</p>
                <p style={{ fontSize: '0.74rem', color: '#64748b', margin: '2px 0 0 0' }}>
                  {answers['H1'] || answers['D2'] ? 'Reported lifetime attacks' : 'Awaiting question response'}
                </p>
              </div>
            </div>

            {/* Criterion B */}
            <div className={`criteria-item ${answers['H2'] ? 'met' : ''}`}>
              <CheckCircleIcon size={16} color={answers['H2'] ? '#059669' : '#94a3b8'} />
              <div>
                <p style={{ fontWeight: 600, margin: 0 }}>Criterion B: 4–72 Hours</p>
                <p style={{ fontSize: '0.74rem', color: '#64748b', margin: '2px 0 0 0' }}>
                  {answers['H2'] ? `Typical attack: ${answers['H2']}h` : 'Awaiting duration response'}
                </p>
              </div>
            </div>

            {/* Criterion C */}
            <div className={`criteria-item ${critCMet >= 2 ? 'met' : ''}`}>
              <CheckCircleIcon size={16} color={critCMet >= 2 ? '#059669' : '#94a3b8'} />
              <div>
                <p style={{ fontWeight: 600, margin: 0 }}>Criterion C: ≥ 2 Pain Features</p>
                <p style={{ fontSize: '0.74rem', color: '#64748b', margin: '2px 0 0 0' }}>
                  Current features met: <b>{critCMet}/4</b> (Unilateral, Throbbing, Mod/Severe, Aggravation)
                </p>
              </div>
            </div>

            {/* Criterion D */}
            <div className={`criteria-item ${critDMet >= 1 ? 'met' : ''}`}>
              <CheckCircleIcon size={16} color={critDMet >= 1 ? '#059669' : '#94a3b8'} />
              <div>
                <p style={{ fontWeight: 600, margin: 0 }}>Criterion D: Associated Symptoms</p>
                <p style={{ fontSize: '0.74rem', color: '#64748b', margin: '2px 0 0 0' }}>
                  Current features met: <b>{critDMet}/2</b> (Nausea/Vomiting, Photophobia + Phonophobia)
                </p>
              </div>
            </div>
          </div>

          {/* Clinician Review Badge */}
          <div style={{
            padding: '12px',
            borderRadius: '10px',
            backgroundColor: '#f1f5f9',
            border: '1px dashed #cbd5e1',
            fontSize: '0.78rem',
            color: '#64748b',
            lineHeight: 1.45
          }}>
            <p style={{ fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
              Treating Neurologist Review
            </p>
            This intake summary will be locked into the clinical report for your doctor to verify before any medical diagnosis is confirmed.
          </div>
        </div>
      </aside>
    </div>
  )
}
