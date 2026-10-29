import React, { useState, useEffect, useRef } from 'react'
import LanguageSelector, { LANGUAGES } from './LanguageSelector'

export default function ChatView({
  sessionCode,
  language,
  onLanguageChange,
  initialBotMessage,
  onOpenClinician,
  onResetSession
}) {
  const [messages, setMessages] = useState([])
  const [currentBotMsg, setCurrentBotMsg] = useState(initialBotMessage)
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(true)
  const [speechErrorNotice, setSpeechErrorNotice] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [isCompleted, setIsCompleted] = useState(false)

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)

  // Initialize Speech Recognition
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
      // Send directly with voice input mode
      handleSendMessage(transcript, 'voice')
    }

    rec.onerror = (event) => {
      setIsListening(false)
      setSpeechErrorNotice('Speech recognition could not capture audio. Please type or tap buttons.')
      setTimeout(() => setSpeechErrorNotice(''), 4000)
    }

    recognitionRef.current = rec
  }, [language])

  // Initial bot message on load
  useEffect(() => {
    if (initialBotMessage) {
      setCurrentBotMsg(initialBotMessage)
      setMessages([{ sender: 'bot', ...initialBotMessage }])
      setProgress(initialBotMessage.progress_percentage || 0)
    }
  }, [initialBotMessage])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Text-to-speech speaker handler
  const speakText = (text) => {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    const langObj = LANGUAGES.find(l => l.code === language) || LANGUAGES[0]
    utterance.lang = langObj.speechCode

    const voices = window.speechSynthesis.getVoices()
    const matchingVoice = voices.find(v => v.lang.startsWith(language) || v.lang === langObj.speechCode)
    if (matchingVoice) utterance.voice = matchingVoice

    window.speechSynthesis.speak(utterance)
  }

  const toggleMic = () => {
    if (!speechSupported) {
      setSpeechErrorNotice('Voice input is not supported in this browser. Please type or use buttons.')
      return
    }
    if (isListening) {
      recognitionRef.current?.stop()
    } else {
      setSpeechErrorNotice('')
      try {
        recognitionRef.current?.start()
      } catch (err) {
        console.warn('Speech recognition start failed:', err)
      }
    }
  }

  const handleSendMessage = async (text, inputMode = 'type', selectedCode = null) => {
    if (!text && selectedCode === null) return
    setIsLoading(true)

    // Append user message to stream
    const userDisplay = selectedCode !== null ? (selectedCode === 'yes' ? 'Yes' : selectedCode === 'no' ? 'No' : String(selectedCode)) : text
    setMessages(prev => [...prev, { sender: 'user', text: userDisplay }])
    setInputText('')

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionCode,
          message: text,
          input_mode: inputMode,
          selected_code: selectedCode
        })
      })

      if (!res.ok) throw new Error('Failed to send message')
      const data = await res.json()
      const botMsg = data.bot_message

      setCurrentBotMsg(botMsg)
      setProgress(botMsg.progress_percentage || progress)
      setMessages(prev => [...prev, { sender: 'bot', ...botMsg }])

      if (botMsg.is_completed) {
        setIsCompleted(true)
      }

      // Auto-speak question if preferred
      if (botMsg.speech_text && inputMode === 'voice') {
        speakText(botMsg.speech_text)
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Connection interrupted. Please tap an option or retry.'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadPatientSummary = () => {
    window.open(`/api/report/pdf/${sessionCode}?for_patient=true`, '_blank')
  }

  const handleDeleteData = async () => {
    if (!window.confirm('Are you sure you want to permanently delete all your symptom data and report?')) return
    try {
      const res = await fetch('/api/privacy/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionCode })
      })
      if (res.ok) {
        alert('All your symptom records have been permanently deleted.')
        onResetSession()
      }
    } catch (err) {
      console.error('Failed deleting data:', err)
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>🧠</span>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary)' }}>
              MigraineAssist
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Code: <b>{sessionCode}</b>
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <LanguageSelector currentLang={language} onLanguageChange={onLanguageChange} />
          <button
            onClick={onOpenClinician}
            className="btn btn-secondary"
            style={{ padding: '6px 10px', fontSize: '0.8rem', minHeight: '34px' }}
            title="Clinician portal login"
          >
            🩺 Doctor Login
          </button>
        </div>
      </header>

      {/* Progress Bar */}
      <div style={{ width: '100%', height: '4px', backgroundColor: '#e2e8f0' }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          backgroundColor: 'var(--primary)',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* Chat Messages Stream */}
      <main className="chat-scroll" aria-live="polite">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`message-bubble ${
              m.sender === 'user' ? 'message-user' : m.is_red_flag_alert ? 'message-urgent' : 'message-bot'
            }`}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {m.text}
              </div>

              {m.sender === 'bot' && (
                <button
                  onClick={() => speakText(m.speech_text || m.text)}
                  className="btn-icon"
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1.1rem',
                    flexShrink: 0
                  }}
                  aria-label="Listen to question"
                  title="Listen to question"
                >
                  🔊
                </button>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-bubble message-bot" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
            Recording response...
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Speech Error Banner */}
      {speechErrorNotice && (
        <div style={{
          backgroundColor: 'var(--warning-amber-light)',
          color: 'var(--warning-amber)',
          padding: '8px 16px',
          fontSize: '0.85rem',
          textAlign: 'center',
          borderTop: '1px solid #fde68a'
        }}>
          {speechErrorNotice}
        </div>
      )}

      {/* Interactive Options Area (Pills) */}
      {!isCompleted && currentBotMsg?.options?.length > 0 && (
        <div style={{
          padding: '8px 16px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          backgroundColor: '#f8fafc',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          {currentBotMsg.options.map((opt) => (
            <button
              key={String(opt.code)}
              className="btn btn-option"
              onClick={() => handleSendMessage('', 'tap', opt.code)}
              disabled={isLoading}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Quick Action Toolbar */}
      <div style={{
        padding: '6px 16px',
        display: 'flex',
        gap: '12px',
        fontSize: '0.85rem',
        backgroundColor: '#ffffff',
        borderTop: '1px solid #e2e8f0',
        overflowX: 'auto'
      }}>
        <button
          onClick={() => handleSendMessage('go back', 'tap')}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          ↩️ Go Back
        </button>
        <button
          onClick={() => handleSendMessage('skip', 'tap')}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          ⏭️ Skip
        </button>
        <button
          onClick={() => handleSendMessage("I don't know", 'tap')}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          ❓ I Don't Know
        </button>
        <button
          onClick={handleDownloadPatientSummary}
          style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          📄 Download Answers PDF
        </button>
        <button
          onClick={handleDeleteData}
          style={{ background: 'none', border: 'none', color: 'var(--urgent-red)', cursor: 'pointer', marginLeft: 'auto' }}
        >
          🗑️ Delete My Data
        </button>
      </div>

      {/* Text & Speech Input Bar */}
      {!isCompleted && (
        <footer className="input-bar">
          <button
            type="button"
            className="btn-icon"
            onClick={toggleMic}
            style={{
              backgroundColor: isListening ? 'var(--urgent-red)' : '#f1f5f9',
              color: isListening ? '#ffffff' : 'var(--text-main)',
              border: isListening ? 'none' : '1px solid var(--border-strong)',
              fontSize: '1.2rem',
              cursor: 'pointer'
            }}
            aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            title={isListening ? 'Listening... click to stop' : 'Click to speak'}
          >
            {isListening ? '⏹️' : '🎙️'}
          </button>

          <input
            type="text"
            className="text-input"
            placeholder={isListening ? 'Listening to your speech...' : 'Type your answer or tap buttons above...'}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage(inputText, 'type')
              }
            }}
            disabled={isLoading}
          />

          <button
            className="btn btn-primary"
            onClick={() => handleSendMessage(inputText, 'type')}
            disabled={isLoading || !inputText.trim()}
          >
            Send
          </button>
        </footer>
      )}

      {/* Completion View */}
      {isCompleted && (
        <div style={{ padding: '24px', textAlign: 'center', backgroundColor: '#f0fdf4' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--success-green)' }}>
            Intake Completed Successfully
          </h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Your answers have been prepared for your doctor's consultation.
          </p>
          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', gap: '12px' }}>
            <button className="btn btn-primary" onClick={handleDownloadPatientSummary}>
              📄 Download Patient Summary PDF
            </button>
            <button className="btn btn-secondary" onClick={onResetSession}>
              Start New Interview
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
