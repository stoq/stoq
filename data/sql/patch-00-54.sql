-- #3802: Remove giftcertificate
DROP VIEW gift_certificate_view;
DROP TABLE gift_certificate_type;
DROP TABLE gift_certificate_adapt_to_sellable;
DROP TABLE gift_certificate;
-- We can't remove it because there might be payments referecing it, so
-- just disable it instead.
UPDATE payment_method SET is_active = FALSE WHERE method_name = 'giftcertificate';

-- Remove the gift certificates themselves
DELETE FROM sale_item 
      USING asellable
      WHERE child_name = 'GiftCertificateAdaptToSellable' AND
            asellable.id = sale_item.sellable_id;
DELETE FROM asellable 
      WHERE child_name = 'GiftCertificateAdaptToSellable';
