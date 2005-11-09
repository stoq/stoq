"""
stoqdrivers/devices/printers/base.py:

    Generic base class implementation for all printers
"""

from zope.interface import providedBy

from stoqdrivers.log import Logger
from stoqdrivers.configparser import FiscalPrinterConfig
from stoqdrivers.exceptions import CriticalError, ConfigError
from stoqdrivers.devices.printers.interface import ICouponPrinter

class BasePrinter(Logger):
    def __init__(self, config_file=None):
        Logger.__init__(self)
        self._load_configuration(config_file)

    def _load_configuration(self, config_file):
        self.config = FiscalPrinterConfig(config_file)

        if not self.config.has_section("Printer"):
            raise ConfigError("There is no printer configured!")

        self.brand = self.config.get_option("brand", "Printer")
        self.baudrate = int(self.config.get_option("baudrate", "Printer"))
        self.model = self.config.get_option("model", "Printer")
        self.device = self.config.get_option("device", "Printer")

        self.debug(("Config data: brand=%s,device=%s,model=%s,baudrate=%s\n"
                    % (self.brand, self.device, self.model, self.baudrate)))

        name = 'stoqdrivers.devices.printers.%s.%s' % (self.brand, self.model)
        try:
            module = __import__(name, None, None, 'stoqdevices')
        except ImportError, reason:
            raise CriticalError(("Could not load driver %s %s: %s"
                                 % (self.brand.capitalize(),
                                    self.model.upper(), reason)))

        class_name = self.model + 'Printer'

        driver_class = getattr(module, class_name, None)
        if not driver_class:
            raise CriticalError(("Printer driver %s needs a class called %s"
                                 % (name, class_name)))

        self._driver = driver_class(device=self.device,
                                    baudrate=self.baudrate)

        driver_interfaces = providedBy(self._driver)
        if not (ICouponPrinter in driver_interfaces):
            raise TypeError("The driver %s doesn't implements a known "
                            "interface")
