-- Care Coordinator Database Schema
-- PostgreSQL/Supabase

-- ============================================
-- SPECIALTIES TABLE
-- ============================================
CREATE TABLE specialties (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    self_pay_rate INTEGER NOT NULL CHECK (self_pay_rate > 0)
);

COMMENT ON TABLE specialties IS 'Medical specialties with associated self-pay rates';

-- ============================================
-- PROVIDERS TABLE
-- ============================================
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    certification TEXT NOT NULL,
    specialty_id INTEGER NOT NULL REFERENCES specialties(id),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE providers IS 'Healthcare providers (doctors, nurses, etc.)';

-- ============================================
-- DEPARTMENTS TABLE
-- ============================================
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    hours TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE departments IS 'Physical locations/clinics where care is provided';

-- ============================================
-- PROVIDER_DEPARTMENTS (Junction Table)
-- ============================================
CREATE TABLE provider_departments (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider_id, department_id)
);

COMMENT ON TABLE provider_departments IS 'Many-to-many: providers can work at multiple locations';

-- ============================================
-- PATIENTS TABLE
-- ============================================
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob TEXT NOT NULL,
    pcp TEXT,
    ehr_id TEXT UNIQUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE patients IS 'Patient demographic information';

-- ============================================
-- INSURANCES TABLE
-- ============================================
CREATE TABLE insurances (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

COMMENT ON TABLE insurances IS 'Accepted insurance providers';

-- ============================================
-- APPOINTMENTS TABLE
-- ============================================
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),
    appointment_type TEXT NOT NULL CHECK (appointment_type IN ('NEW', 'ESTABLISHED')),
    date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'completed', 'cancelled', 'noshow')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE appointments IS 'All appointments - past and future';

-- ============================================
-- REFERRALS TABLE (Optional - for tracking)
-- ============================================
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    provider_id INTEGER REFERENCES providers(id),
    specialty_id INTEGER NOT NULL REFERENCES specialties(id),
    date_referred TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'completed')),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE referrals IS 'Track which patients need which specialty appointments';

-- ============================================
-- INDEXES for Performance
-- ============================================
CREATE INDEX idx_providers_specialty ON providers(specialty_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_provider ON appointments(provider_id);
CREATE INDEX idx_appointments_date ON appointments(date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_provider_departments_provider ON provider_departments(provider_id);
CREATE INDEX idx_provider_departments_department ON provider_departments(department_id);