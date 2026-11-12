import React, { useState } from 'react'
import ConsentScreen from './components/ConsentScreen'
import ChatView from './components/ChatView'
import RedFlagModal from './components/RedFlagModal'
import ClinicianPortal from './components/ClinicianPortal'

export default function App() {
  const [currentView, setCurrentView] = useState('consent') // 'consent', 'chat', 'clinician'
  const [sessionCode, setSessionCode] = useState('')
  const [language, setLanguage] = useState('en')
  const [initialBotMsg, setInitialBotMsg] = useState(null)
  const [chatHistory, setChatHistory] = useState([])
  const [sessionAnswers, setSessionAnswers] = useState({})
  const [showRedFlagModal, setShowRedFlagModal] = useState(false)
  const [redFlagText, setRedFlagText] = useState('')

  const handleStartSession = async (researchConsent) => {
    try {
      const res = await fetch('/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language,
          research_consent: researchConsent
        })
      })
      if (!res.ok) throw new Error('Failed to start session')
      const data = await res.json()
      setSessionCode(data.session_id)
      setInitialBotMsg(data.bot_message)
      setChatHistory([])
      setSessionAnswers({})
      setCurrentView('chat')
    } catch (err) {
      console.error('Error starting session:', err)
      alert('Could not start intake session. Please check if the backend server is running.')
    }
  }

  const handleResumeSession = async (code) => {
    try {
      const res = await fetch('/api/session/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: code })
      })
      if (!res.ok) throw new Error('Session code not found')
      const data = await res.json()
      setSessionCode(data.session_id)
      setLanguage(data.language)
      setInitialBotMsg(data.bot_message)
      setChatHistory(data.chat_history || [])
      setSessionAnswers(data.answers || {})

      if (data.status === 'urgent_red_flag') {
        setRedFlagText(data.bot_message?.text || '')
        setShowRedFlagModal(true)
      } else {
        setShowRedFlagModal(false)
      }

      setCurrentView('chat')
    } catch (err) {
      console.error('Error resuming session:', err)
      alert('Invalid or expired session code. Please verify and try again.')
    }
  }

  const handleLanguageChange = async (newLang) => {
    setLanguage(newLang)
    if (sessionCode) {
      try {
        const res = await fetch('/api/session/language', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionCode,
            language: newLang
          })
        })
        if (res.ok) {
          const data = await res.json()
          setInitialBotMsg(data.bot_message)
        }
      } catch (err) {
        console.error('Error changing language:', err)
      }
    }
  }

  const handleDownloadUrgentReport = () => {
    if (sessionCode) {
      window.open(`/api/report/pdf/${sessionCode}`, '_blank')
    }
  }

  const handleResetSession = () => {
    setSessionCode('')
    setInitialBotMsg(null)
    setChatHistory([])
    setSessionAnswers({})
    setShowRedFlagModal(false)
    setCurrentView('consent')
  }

  return (
    <div>
      {currentView === 'consent' && (
        <ConsentScreen
          currentLang={language}
          onStartSession={handleStartSession}
          onResumeSession={handleResumeSession}
        />
      )}

      {currentView === 'chat' && (
        <ChatView
          sessionCode={sessionCode}
          language={language}
          onLanguageChange={handleLanguageChange}
          initialBotMessage={initialBotMsg}
          initialChatHistory={chatHistory}
          initialAnswers={sessionAnswers}
          onResumeSession={handleResumeSession}
          onOpenClinician={() => setCurrentView('clinician')}
          onResetSession={handleResetSession}
        />
      )}

      {currentView === 'clinician' && (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', backgroundColor: '#f1f5f9' }}>
          <ClinicianPortal
            onClose={() => setCurrentView(sessionCode ? 'chat' : 'consent')}
          />
        </div>
      )}

      {showRedFlagModal && (
        <RedFlagModal
          sessionCode={sessionCode}
          redFlagMessage={redFlagText}
          onDownloadReport={handleDownloadUrgentReport}
        />
      )}
    </div>
  )
}
