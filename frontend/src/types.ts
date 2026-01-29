export interface Patient {
  id: number
  name: string
  dob: string
  pcp: string
  ehrId: string
  notes: string
  insurance?: {
    id: number
    name: string
    accepted: boolean
  }
  referred_providers?: Array<{
    specialty: string
    provider?: string
  }>
  appointments?: Array<{
    date: string
    provider: string
    status: string
  }>
}

export interface Message {
  text: string
  sender: 'agent' | 'nurse'
  timestamp: Date
}
