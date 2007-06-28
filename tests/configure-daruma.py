from decimal import Decimal

from stoqdrivers.enum import TaxType

from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.database.runtime import get_current_station, new_transaction
from stoqlib.domain.devices import DeviceConstant, DeviceSettings

trans = new_transaction()
station = get_current_station(trans)
assert station
for value in [0.18, 0.12, 0.5]:
    SellableTaxConstant(description='%2.2f %%' % (value,),
                        tax_type=int(TaxType.CUSTOM),
                        tax_value=value,
                        connection=trans)

settings = DeviceSettings(station=station,
                          device=DeviceSettings.DEVICE_SERIAL1,
                          brand='daruma',
                          model='FS345',
                          type=DeviceSettings.FISCAL_PRINTER_DEVICE,
                          connection=trans)
settings.create_fiscal_printer_constants()

for device_value, value in  [('TA', Decimal("0.18")),
                             ('TB', Decimal("0.12")),
                             ('TC', Decimal("0.05"))]:
    DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
                   constant_name='%d %%' % (value,),
                   constant_value=value,
                   constant_enum=int(TaxType.CUSTOM),
                   device_value=device_value,
                   device_settings=settings,
                   connection=trans)
DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
               constant_name="5 % (ISS)",
               constant_value=5,
               constant_enum=int(TaxType.SERVICE),
               device_value='Td',
               device_settings=settings,
               connection=trans)

trans.commit()


