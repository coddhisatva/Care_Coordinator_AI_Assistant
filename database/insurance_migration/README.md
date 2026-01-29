# Insurance Migration

## Overview
This migration adds insurance tracking functionality:
- Insurances can exist in the system whether accepted or not (new `accepted` boolean)
- Patients can be linked to their insurance provider
- Agent can set/update patient insurance dynamically.

## Changes Made

### 1. Database Schema Changes (`insurance_migration.sql`)
- Added `accepted` boolean to `insurances` table (tracks which insurances hospital accepts)
- Added `insurance_id` foreign key to `patients` table (links patient to their insurance)
- Assigned existing patients to insurances:
  - John Doe → Blue Cross Blue Shield of North Carolina
  - Jane Smith → Medicaid (if exists)

### 2. New API Endpoint (`flask-app.py`)
**POST `/api/set_patient_insurance`**
- Sets or updates patient's insurance
- Creates new insurance record if doesn't exist (marked `accepted=false`)
- Returns whether insurance is accepted

### 3. New Agent Tool (`tools.py`)
**`set_patient_insurance(patient_id, insurance_name)`**
- Allows agent to set patient insurance during conversation
- Example: Nurse says "Patient has Cigna" → Agent calls tool → Updates patient record
- Returns acceptance status so agent can inform about self-pay if needed

### 4. Updated Existing Code

**`check_insurance` tool** - Now filters by `accepted=TRUE`:
```python
sql = "SELECT name FROM insurances WHERE accepted = TRUE"
```

**`/patient/<id>` endpoint** - Now returns insurance info:
```json
{
  "id": 1,
  "name": "John Doe",
  "insurance": {
    "id": 3,
    "name": "Blue Cross Blue Shield of North Carolina",
    "accepted": true
  }
}
```

**`Patient` class** - Now includes insurance field

**`config.py`** - Added `set_patient_insurance` to available tools

## How to Run Migration

### Step 1: Apply Database Changes
Go to your Supabase dashboard → SQL Editor → New Query

Copy and paste contents of `database/insurance_migration/insurance_migration.sql` and execute.

### Step 2: Verify Migration  
Run these queries in Supabase SQL Editor:

```sql
-- Check insurances have 'accepted' column
SELECT * FROM insurances;

-- Check patients have insurance assigned
SELECT 
    p.id, 
    p.first_name, 
    p.last_name, 
    i.name as insurance, 
    i.accepted 
FROM patients p 
LEFT JOIN insurances i ON p.insurance_id = i.id;
```

### Step 3: Restart Flask API
```bash
cd api
python flask-app.py
```

### Step 4: Test New Endpoint
```bash
# Test setting insurance
curl -X POST http://localhost:5000/api/set_patient_insurance \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1, "insurance_name": "Cigna"}'

# Should return:
# {
#   "success": true,
#   "insurance_name": "Cigna",
#   "accepted": true,
#   "message": "Patient insurance set to Cigna"
# }
```

## Usage in Agent

The agent can now:

1. **Check patient insurance on load:**
```
Agent: "Hi! I see John Doe has Blue Cross Blue Shield (accepted). 
       Ready to book an appointment for Orthopedics?"
```

2. **Handle insurance updates:**
```
Nurse: "Patient has Humana insurance"
Agent: [calls set_patient_insurance(1, "Humana")]
Agent: "I've updated the insurance to Humana. Note: This insurance 
       is not currently accepted. Self-pay for Orthopedics is $300."
```

3. **Proactively warn about non-accepted insurance:**
```
Agent: "⚠️ Note: This patient's insurance (SuperCare) is not accepted. 
       Self-pay for Primary Care is $150."
```

## Tool Count Update
Total tools: **9** (was 8)
- get_providers_by_specialty
- get_provider_locations
- get_available_times
- check_appointment_history
- check_insurance
- get_self_pay_rate
- **set_patient_insurance** ← NEW
- book_appointment
- query_database
