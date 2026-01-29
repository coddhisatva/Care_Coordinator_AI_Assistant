-- Clear all appointments from the database
-- Run this to remove test/demo appointments

DELETE FROM appointments;

-- Verify deletion
SELECT COUNT(*) as remaining_appointments FROM appointments;
