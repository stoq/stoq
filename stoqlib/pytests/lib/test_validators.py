from stoqlib.lib import validators


def test_validate_phone_number():
    assert validators.validate_phone_number(0) is False


def test_validate_postal_code():
    assert validators.validate_postal_code("") is False


def test_validate_are_code():
    assert validators.validate_area_code("12345678") is False


def test_validate_email():
    assert validators.validate_email("") is False
    assert validators.validate_email("dev@stoq.com.br") is True


def test_validate_vehicle_license_plate():
    assert validators.validate_vehicle_license_plate("") is False
    assert validators.validate_vehicle_license_plate("DCG1234")
