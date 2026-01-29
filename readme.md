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
├── database/              # Database setup scripts (Phase 1) ✅
│   ├── schema.sql
│   ├── parse_data_sheet.py
│   ├── seed_database.py
│   └── test_db.py
│
├── api/                   # Backend API (Phase 2) ✅
│   ├── flask-app.py
│   └── test_api.py
│
├── agent/                 # AI Agent & Tools (Phase 3) - Partial
│   ├── agent.py          ✅ Core Agent class
│   ├── tools.py          ✅ 8 tool implementations
│   ├── config.py         ✅ System prompt & settings
│   ├── appointment_state.py  ✅ State management
│   ├── test_agent.py     ✅ Testing script
│   └── run_agent.py      ⚠️ TODO - Agent server/main loop
│
├── frontend/              # React UI (Phase 4) - TODO
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

# PostgreSQL Connection (for agent tools)
# Get from: Supabase Dashboard → Database → Connection Pooling → Session pooler
POSTGRES_CONNECTION_STRING=postgresql://postgres.xxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# OpenAI (for agent)
OPENAI_API_KEY=sk-your-key-here
```

**Note:** You need the Session pooler connection string, not Direct connection.

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

## Phase 2: Backend API ✅

### Overview
Flask API extended with Supabase integration providing endpoints for agent tools to query data and book appointments.

### Endpoints
- `GET /` - Health check
- `GET /patient/<id>` - Get patient information with appointments and referrals
- `POST /api/query` - Execute SQL SELECT queries (for agent tools)
- `POST /api/book` - Book appointments

### Setup Instructions

1. **Ensure database is set up** (Phase 1 complete)

2. **Install dependencies**
```bash
pip install flask flask-cors psycopg2-binary
```

3. **Add PostgreSQL connection string to .env**

Get Session Pooler connection string from Supabase:
- Dashboard → Database → Connection Pooling → Session pooler
- Copy the full URI

Add to `.env`:
```bash
POSTGRES_CONNECTION_STRING=postgresql://postgres.xxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

4. **Run Flask API**
```bash
cd api
python flask-app.py
```

Should see:
```
✓ Connected to Supabase
✓ Connected to PostgreSQL for raw SQL queries
Starting Flask server on http://localhost:5000
```

5. **Test API**
```bash
python test_api.py
```

All 4 tests should pass.

### API Details

**GET /patient/\<id\>**
- Returns patient demographics, referrals, and appointment history
- Queries Supabase with JOINs for complete data
- Used by agent to load patient context

**POST /api/query**
- Accepts SQL SELECT queries with parameterized inputs
- Executes via PostgreSQL connection for flexibility
- Used by agent tools for custom queries
- Security: Only allows SELECT statements

**POST /api/book**
- Books new appointment
- Validates all required fields
- Calculates arrival time based on appointment type
- Returns confirmation with appointment details

### Troubleshooting

**"Database connection not configured"**
- Check POSTGRES_CONNECTION_STRING in .env
- Verify you're using Session pooler connection (not Direct connection)
- Restart Flask after updating .env

---

## Phase 3: AI Agent & Tools (PARTIAL - run_agent.py TODO)

### Overview
OpenAI-powered conversational agent with tool-calling capabilities. Agent maintains conversation context, determines appointment requirements, and coordinates booking workflow.

### Components Completed ✅

**agent.py** - Core Agent class
- Conversation loop with OpenAI GPT-4
- Tool call parsing and execution
- Message history management
- Max iteration safety (stops at 10 calls)
- Booking state tracking

**tools.py** - 8 Tool implementations
- `get_providers_by_specialty` - Find providers by specialty
- `get_provider_locations` - Get provider work locations  
- `get_available_times` - Check appointment availability (single date or range)
- `check_appointment_history` - Determine NEW vs ESTABLISHED
- `check_insurance` - Verify insurance acceptance
- `get_self_pay_rate` - Get cost without insurance
- `book_appointment` - Final booking action
- `query_database` - General SQL queries for flexibility

All tools make HTTP requests to Flask API endpoints.

**config.py** - Configuration
- Complete system prompt with business rules
- Tool definitions
- Agent settings (model, max iterations)

**appointment_state.py** - State management
- `Patient` class - holds patient data from API
- `AppointmentBooking` class - tracks booking progress
- Helper methods for validation and formatting

**test_agent.py** - Testing script
- Interactive mode: chat with agent in terminal
- Automated scenarios: run test conversations
- Commands: `status`, `reset`, `quit`

### Component Still TODO ⚠️

**run_agent.py** - Agent server (main loop)
- WebSocket server for frontend connection
- Agent lifecycle management
- Session persistence
- Main conversation loop

This will be completed before Phase 4 (Frontend).

### Setup Instructions (Current Testing)

1. **Install dependencies**
```bash
pip install openai
```

2. **Add OpenAI key to .env**
```bash
OPENAI_API_KEY=sk-your-key-here
```

3. **Test agent in terminal**

Terminal 1 - Run Flask API:
```bash
cd api
python flask-app.py
```

Terminal 2 - Run agent test:
```bash
cd agent
python test_agent.py
```

Choose option 1 (Interactive) or 2 (Automated scenarios).

### Testing

**Interactive Mode:**
```
Nurse: I need to book orthopedics
Agent: I see John has a referral for Orthopedics with Dr. House. Let me find available times...
```

**Commands:**
- Type messages to chat with agent
- `status` - Show current booking progress
- `reset` - Clear conversation and start over
- `quit` - Exit

### Agent Behavior
## Dev's notes: Workflow is still being determined. Don't necessarily trust below here.
## Most files within agent.py prob need to be changed, including sys prompt in config, and making the actual file run_agent.py which contains the agent instance and flow/loop.
## We curr have a test_agent.py file. Dev has ignored this so far. Unsure if it will help us or be worthwhile. 

**Workflow:**
1. Understands nurse's request (uses patient referrals for context)
2. Makes tool calls to gather information
3. Presents options to nurse (doesn't make decisions for them)
4. Collects missing information through conversation
5. Validates all requirements met
6. Books appointment
7. Provides confirmation

**Business Logic:**
- Determines NEW vs ESTABLISHED by checking 5-year history
- Only books when all required fields collected
- Validates times against office hours
- Provides self-pay rates when insurance not accepted

### Troubleshooting

**"OPENAI_API_KEY not found"**
- Add to .env file in root directory
- Restart terminal/load environment

**Agent makes too many tool calls**
- System prompt includes 6-call warning
- Hard limit at 10 iterations
- Check if agent is stuck in loop

**Tool calls fail**
- Ensure Flask API is running
- Check API endpoints return 200 status

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

**Agent (Interactive Testing):**
```bash
# Terminal 1: Flask API must be running first
cd api
python flask-app.py

# Terminal 2: Run agent test
cd agent
python test_agent.py
```

**Frontend:** *(Phase 4 - not yet implemented)*
```bash
cd frontend
npm run dev
# Will run on http://localhost:5173
```

### Testing

**Database:**
```bash
cd database
python test_db.py
```

**API:**
```bash
cd api
python test_api.py
```

**Agent:**
```bash
cd agent
python test_agent.py
# Choose: 1) Interactive, 2) Automated, or 3) Both
```

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