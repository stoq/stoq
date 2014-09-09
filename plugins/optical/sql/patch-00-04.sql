ALTER TABLE optical_medic ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_product ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_work_order ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_history ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_measures ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_test ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_visual_acuity ALTER COLUMN te_id SET DEFAULT new_te();
