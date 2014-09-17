ALTER TABLE optical_medic ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_product ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_work_order ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_history ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_measures ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_test ALTER COLUMN te_id SET DEFAULT new_te();
ALTER TABLE optical_patient_visual_acuity ALTER COLUMN te_id SET DEFAULT new_te();

CREATE RULE update_te AS ON UPDATE TO optical_medic DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_product DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_work_order DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_patient_history DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_patient_measures DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_patient_test DO ALSO SELECT update_te(old.te_id);
CREATE RULE update_te AS ON UPDATE TO optical_patient_visual_acuity DO ALSO SELECT update_te(old.te_id);

