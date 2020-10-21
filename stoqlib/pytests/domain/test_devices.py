from stoqlib.domain.devices import DeviceSettings


def test_device_settings_is_valid(store, current_station):
    device = DeviceSettings(store=store,
                            device_name=u'usb:0xa:0x1',
                            type=DeviceSettings.NON_FISCAL_PRINTER_DEVICE,
                            station=current_station)

    assert device.is_valid() is False

    device.model = "foo"
    device.brand = "bar"

    assert device.is_valid() is True
