-- Remove past_emission_date constraint, as datetime.now() may be diferent from NOW().

ALTER TABLE ecf_document_history DROP CONSTRAINT past_emission_date;
