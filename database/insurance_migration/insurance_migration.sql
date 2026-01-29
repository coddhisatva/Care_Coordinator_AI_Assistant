-- Insurance Migration
-- Adds 'accepted' boolean to insurances table (track which insurances are accepted vs just known)
-- Adds 'insurance_id' to patients table (link patient to their insurance)

-- Step 1: Add 'accepted' column to insurances table
ALTER TABLE insurances 
ADD COLUMN accepted BOOLEAN DEFAULT TRUE;

-- Step 2: Mark existing insurances as accepted (since they were seeded as accepted ones)
UPDATE insurances 
SET accepted = TRUE;

-- Step 3: Add insurance_id to patients table
ALTER TABLE patients 
ADD COLUMN insurance_id INTEGER REFERENCES insurances(id);

-- Step 4: Assign insurance to existing patients
-- John Doe - Blue Cross Blue Shield of North Carolina
UPDATE patients 
SET insurance_id = (
    SELECT id FROM insurances 
    WHERE name = 'Blue Cross Blue Shield of North Carolina'
)
WHERE id = 1;

-- Jane Smith - Medicaid (if she exists)
UPDATE patients 
SET insurance_id = (
    SELECT id FROM insurances 
    WHERE name = 'Medicaid'
)
WHERE id = 2 AND EXISTS (SELECT 1 FROM patients WHERE id = 2);

-- Verification queries (run these to check migration worked)
-- SELECT * FROM insurances;
-- SELECT p.id, p.first_name, p.last_name, i.name as insurance, i.accepted 
-- FROM patients p 
-- LEFT JOIN insurances i ON p.insurance_id = i.id;
