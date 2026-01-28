# Care Coordinator Assistant

An AI-powered conversational agent that helps hospital nurses book patient appointments, answer questions about providers, insurance, and availability, and navigate complex scheduling rules.

## Overview

This project implements an intelligent care coordination system that:
- Guides nurses through appointment booking workflows
- Answers questions about providers, locations, insurance coverage
- Determines appointment types (NEW vs ESTABLISHED) based on patient history
- Validates scheduling against office hours and availability
- Handles edge cases and exceptions intelligently

### Demo Scenario
A nurse needs to book follow-up appointments for patient John Doe after a hospital visit requiring orthopedic and primary care consultations.

## Tech Stack

**Backend:**
- PostgreSQL (Supabase) - Database
- Flask - REST API
- Python 3.9+

**AI Agent:**
- OpenAI GPT-4 - Conversational AI
- Custom tool-calling framework

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- shadcn/ui components

## Project Structure

```
care-coordinator/
├── database/              # Database setup scripts (Phase 1)
│   ├── schema.sql
│   ├── parse_data_sheet.py
│   ├── seed_database.py
│   └── test_db.py
│
├── api/                   # Backend API (Phase 2)
│   └── flask-app.py
│
├── agent/                 # AI Agent & Tools (Phase 3)
│   ├── agent.py
│   ├── tools.py
│   ├── config.py
│   └── appointment_state.py
│
├── frontend/              # React UI (Phase 4)
│   └── src/
│
├── data_sheet.txt         # Hospital reference data
├── .env                   # Environment variables (gitignored)
├── requirements.txt       # Python dependencies
└── README.md
```

## Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- Supabase account
- OpenAI API key

### 1. Clone & Install Dependencies

```bash
git clone <repository-url>
cd care-coordinator

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (Phase 4)
cd frontend
npm install
cd ..
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OpenAI
OPENAI_API_KEY=sk-your-key-here
```

---

## Phase 1: Database Setup ✅

### Overview
Set up Supabase PostgreSQL database with hospital data including providers, departments, patients, appointments, and business rules.

### Database Schema

**Tables:**
- `specialties` - Medical specialties with self-pay rates
- `providers` - Healthcare providers (doctors, nurses)
- `departments` - Physical clinic locations
- `provider_departments` - Many-to-many: providers work at multiple locations
- `patients` - Patient demographics and preferences
- `appointments` - All appointments (past and future)
- `insurances` - Accepted insurance providers
- `referrals` - Patient referrals tracking (optional)

### Setup Instructions

1. **Apply Database Schema**

Go to your Supabase dashboard → SQL Editor → New Query

Copy and paste contents of `database/schema.sql` and run it.

2. **Seed Database**

```bash
cd database
python seed_database.py
```

This will:
- Parse `data_sheet.txt`
- Populate all tables with hospital data
- Create sample patients (John Doe, Jane Smith)
- Add appointment history

3. **Verify Setup**

```bash
python test_db.py
```

All tests should pass. You should see:
```
✓ ALL TESTS PASSED!
Database is ready for use!
```

### Database Details

**Sample Data Seeded:**
- 3 specialties (Primary Care, Orthopedics, Surgery)
- 5 providers (Dr. Grey, Dr. House, Dr. Yang, Dr. Perry, Dr. Brennan)
- 5 departments/locations across North Carolina
- 2 patients with appointment history
- 5 accepted insurance plans

**Key Design Decisions:**
- Normalized schema with proper foreign keys
- Specialties stored with rates (no separate rates table)
- Appointments store both appointment_time and arrival_time
- Dates in ISO format (YYYY-MM-DD) for proper sorting
- Indexes on frequently queried columns (foreign keys, dates, status)

### Troubleshooting

**"Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"**
- Ensure `.env` file exists in root directory
- Check variables are set correctly (no quotes needed)

**"relation does not exist"**
- Schema hasn't been applied
- Run `schema.sql` in Supabase SQL Editor first

**Parser fails**
- Check `data_sheet.txt` exists in root directory
- Verify each provider section starts with `- LastName, FirstName`

---

## Phase 2: Backend API (TODO)

### Overview
Extend Flask API to connect to Supabase and provide endpoints for querying data and booking appointments.

### Endpoints (Planned)
- `GET /patient/<id>` - Get patient information (existing)
- `POST /api/query` - Execute SQL queries
- `POST /api/book` - Book appointments
- `GET /health` - Health check

### Setup Instructions
*(To be completed)*

---

## Phase 3: AI Agent & Tools (TODO)

### Overview
Implement OpenAI-powered conversational agent with tool-calling capabilities.

### Tools (Planned)
- `get_providers_by_specialty` - Find providers by specialty
- `get_provider_locations` - Get provider work locations
- `get_available_times` - Check appointment availability
- `check_appointment_history` - Determine NEW vs ESTABLISHED
- `check_insurance` - Verify insurance acceptance
- `get_self_pay_rate` - Get cost without insurance
- `book_appointment` - Final booking
- `query_database` - General SQL queries

### Setup Instructions
*(To be completed)*

---

## Phase 4: Frontend UI (TODO)

### Overview
React-based web interface for nurses to interact with the care coordinator assistant.

### Features (Planned)
- Patient information sidebar
- Chat interface with AI agent
- Booking progress tracker
- Debug panel for tool calls

### Setup Instructions
*(To be completed)*

---

## Development Workflow

### Running Locally

**Backend API:**
```bash
cd api
python flask-app.py
# Runs on http://localhost:5000
```

**Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### Testing

**Database:**
```bash
cd database
python test_db.py
```

**API:** *(To be added in Phase 2)*

**Agent:** *(To be added in Phase 3)*

---

## Design Decisions

### Why Supabase?
- PostgreSQL with instant APIs
- Easy to set up and manage
- Good developer dashboard
- Scales well from prototype to production

### Why HTTP API Layer?
- Simulates production architecture where multiple apps access same data
- Provides security, validation, and audit trail layer
- Allows for future scalability (multiple clients, rate limiting, etc.)

### Why Specialized + General Tools?
- Specialized tools (`get_provider_locations`) for common operations
- General SQL tool for flexibility when patterns don't fit
- Balances ease-of-use with power

### Why React + TypeScript?
- Type safety prevents runtime errors
- Component-based architecture is maintainable
- Large ecosystem of libraries
- Familiar to most developers

---

## Business Rules

**Appointment Types:**
- **NEW**: 30 minutes, patient hasn't seen provider in 5+ years
- **ESTABLISHED**: 15 minutes, patient has seen provider in last 5 years

**Arrival Times:**
- NEW patients: 30 minutes early
- ESTABLISHED patients: 10 minutes early

**Office Hours:**
- Appointments can only be booked within office hours
- Hours vary by location (see departments table)

**Accepted Insurance:**
- Medicaid
- United Health Care
- Blue Cross Blue Shield of North Carolina
- Aetna
- Cigna

**Self-Pay Rates:**
- Primary Care: $150
- Orthopedics: $300
- Surgery: $1000

---

## Future Enhancements

- [ ] Voice interface (speech-to-text)
- [ ] Real-time provider schedule integration
- [ ] Patient SMS/email confirmations
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Provider preference learning
- [ ] Insurance verification API integration

---

## Contributing

*(To be added)*

## License

*(To be added)*

## Contact

*(To be added)*