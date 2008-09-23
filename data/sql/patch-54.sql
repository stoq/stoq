-- #3802: Remove giftcertificate
DROP VIEW IF EXISTS gift_certificate_view;
DROP TABLE gift_certificate_type;
DROP TABLE gift_certificate_adapt_to_sellable;
DROP TABLE gift_certificate;
-- We can't remove it because there might be payments referecing it, so
-- just disable it instead.
UPDATE payment_method SET is_active = FALSE WHERE method_name = 'giftcertificate';
