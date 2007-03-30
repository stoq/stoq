from decimal import Decimal

from stoqdrivers.enum import TaxType

from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.database.runtime import get_current_station, new_transaction
from stoqlib.domain.devices import DeviceConstant, DeviceSettings

trans = new_transaction()
station = get_current_station(trans)
assert station
for value in [25, 17, 12, 8, 5]:
    SellableTaxConstant(description='%d %%' % (value,),
                        tax_type=TaxType.CUSTOM,
                        tax_value=value,
                        connection=trans)

settings = DeviceSettings(station=station,
                          device=DeviceSettings.DEVICE_SERIAL1,
                          brand='perto',
                          model='Pay2023',
                          type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                          connection=trans)
settings.create_fiscal_printer_constants()

for device_value, value in  [('\x80', Decimal(17)),
                             ('\x81', Decimal(12)),
                             ('\x82', Decimal(25)),
                             ('\x83', Decimal(8)),
                             ('\x84', Decimal(5))]:
    DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
                   constant_name='%d %%' % (value,),
                   constant_value=value,
                   constant_enum=TaxType.CUSTOM,
                   device_value=device_value,
                   device_settings=settings,
                   connection=trans)
DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
               constant_name="3 % (ISS)",
               constant_value=3,
               constant_enum=TaxType.SERVICE,
               device_value='\x85',
               device_settings=settings,
               connection=trans)

# Check if we have a virtual printer, if so we must remove it
settings = DeviceSettings.get_virtual_printer_settings(
    trans, station)
if settings:
    DeviceSettings.delete(settings.id, connection=trans)

trans.commit()


