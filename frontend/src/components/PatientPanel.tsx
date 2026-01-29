import { Patient } from '../types'

interface PatientPanelProps {
  patient: Patient | null
}

export default function PatientPanel({ patient }: PatientPanelProps) {
  if (!patient) {
    return (
      <div className="p-6">
        <div className="text-gray-500">Loading patient information...</div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Patient Information</h2>
      
      {/* Demographics */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-700 mb-2">Demographics</h3>
        <div className="space-y-1 text-sm">
          <div><span className="font-medium">Name:</span> {patient.name}</div>
          <div><span className="font-medium">DOB:</span> {patient.dob}</div>
          <div><span className="font-medium">PCP:</span> {patient.pcp}</div>
          <div><span className="font-medium">EHR ID:</span> {patient.ehrId}</div>
        </div>
      </div>

      {/* Insurance */}
      {patient.insurance && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-700 mb-2">Insurance</h3>
          <div className="text-sm">
            <div>{patient.insurance.name}</div>
            {!patient.insurance.accepted && (
              <div className="text-red-600 font-medium mt-1">⚠️ Not Accepted - Self Pay</div>
            )}
          </div>
        </div>
      )}

      {/* Referrals */}
      {patient.referred_providers && patient.referred_providers.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-700 mb-2">Referrals</h3>
          <div className="space-y-2">
            {patient.referred_providers.map((ref, idx) => (
              <div key={idx} className="text-sm bg-blue-50 p-2 rounded">
                <div className="font-medium">{ref.specialty}</div>
                {ref.provider && <div className="text-gray-600">{ref.provider}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {patient.notes && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-700 mb-2">Notes</h3>
          <div className="text-sm text-gray-600">{patient.notes}</div>
        </div>
      )}

      {/* Recent Appointments */}
      {patient.appointments && patient.appointments.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-700 mb-2">Recent Appointments</h3>
          <div className="space-y-2">
            {patient.appointments.slice(0, 5).map((apt, idx) => (
              <div key={idx} className="text-sm border-l-2 border-gray-300 pl-2">
                <div className="font-medium">{apt.date}</div>
                <div className="text-gray-600">{apt.provider}</div>
                <div className="text-xs text-gray-500">{apt.status}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
