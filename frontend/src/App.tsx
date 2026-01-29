import { useState, useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import PatientPanel from './components/PatientPanel'
import ChatInterface from './components/ChatInterface'
import { Patient, Message } from './types'

const AGENT_URL = import.meta.env.VITE_AGENT_URL || 'http://localhost:5001'

function App() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)
  const [patient, setPatient] = useState<Patient | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [debugMode, setDebugMode] = useState(false)
  const [bookingProgress, setBookingProgress] = useState<string>('')
  const [currentPatientId, setCurrentPatientId] = useState('1')
  
  const getUserId = () => {
    let userId = localStorage.getItem('nurse_user_id')
    if (!userId) {
      userId = 'nurse_' + Math.random().toString(36).substring(7)
      localStorage.setItem('nurse_user_id', userId)
    }
    return userId
  }

  useEffect(() => {
    const userId = getUserId()
    
    const newSocket = io(AGENT_URL, {
      query: {
        user_id: userId,
        patient_id: currentPatientId
      }
    })

    newSocket.on('connect', () => {
      console.log('Connected to agent')
      setConnected(true)
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from agent')
      setConnected(false)
    })

    newSocket.on('message', (data: { text: string, patient_name?: string, booking_progress?: string }) => {
      setMessages(prev => [...prev, {
        text: data.text,
        sender: 'agent',
        timestamp: new Date()
      }])
      
      if (data.patient_name && !patient) {
        // First message with patient name - we'll load patient data separately
        loadPatientData(currentPatientId)
      }
      
      if (data.booking_progress) {
        setBookingProgress(data.booking_progress)
      }
    })

    newSocket.on('error', (data: { message: string }) => {
      console.error('Agent error:', data.message)
      alert('Error: ' + data.message)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [currentPatientId])

  const loadPatientData = async (patientId: string) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/patient/${patientId}`)
      if (response.ok) {
        const data = await response.json()
        setPatient(data)
      }
    } catch (error) {
      console.error('Failed to load patient data:', error)
    }
  }

  const sendMessage = (text: string) => {
    if (!socket || !connected) return
    
    setMessages(prev => [...prev, {
      text,
      sender: 'nurse',
      timestamp: new Date()
    }])
    
    socket.emit('message', { text })
  }

  const resetChat = () => {
    if (!socket || !connected) return
    setMessages([])
    setBookingProgress('')
    socket.emit('reset')
  }

  const nextPatient = () => {
    if (!socket || !connected) return
    
    const nextId = String(parseInt(currentPatientId) + 1)
    setCurrentPatientId(nextId)
    setMessages([])
    setBookingProgress('')
    setPatient(null)
    
    // Reconnect with new patient
    socket.close()
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white px-6 py-4 shadow-md">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Care Coordinator Assistant</h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`}></span>
              <span className="text-sm">{connected ? 'Connected' : 'Disconnected'}</span>
            </div>
            <button
              onClick={() => setDebugMode(!debugMode)}
              className="px-3 py-1 bg-blue-500 hover:bg-blue-400 rounded text-sm"
            >
              {debugMode ? 'Hide' : 'Show'} Debug
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Patient Panel */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <PatientPanel patient={patient} />
        </div>

        {/* Chat Interface */}
        <div className="flex-1 flex flex-col">
          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            onReset={resetChat}
            onNextPatient={nextPatient}
            connected={connected}
          />
        </div>

        {/* Debug Panel */}
        {debugMode && (
          <div className="w-80 bg-gray-100 border-l border-gray-200 overflow-y-auto p-4">
            <h3 className="font-semibold text-lg mb-3">Debug Panel</h3>
            <div className="mb-4">
              <h4 className="font-medium text-sm text-gray-700 mb-1">Booking Progress</h4>
              <pre className="text-xs bg-white p-2 rounded border border-gray-300 whitespace-pre-wrap">
                {bookingProgress || 'No booking in progress'}
              </pre>
            </div>
            <div>
              <h4 className="font-medium text-sm text-gray-700 mb-1">Connection Info</h4>
              <div className="text-xs bg-white p-2 rounded border border-gray-300">
                <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
                <div>Patient ID: {currentPatientId}</div>
                <div>User ID: {getUserId()}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
