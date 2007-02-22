# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Adriano Monteiro        <adriano@globalret.com.br>
##
"""
Base logging module
"""

import sys
import logging

from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

log_level = logging.CRITICAL

class Log(logging.Logger):
    def __init__(self, file=sys.stdout, level=log_level,
                 category='stoqdrivers'):
        """Initializes Log module, creating log handler and defining log
        level.

        level attribute is not mandatory. It defines from which level
        messages should be logged. Logs with lower level are ignored.

        logging default levels table:

        Level                                         Numeric Value
        logging.NOTSET                                0
        logging.DEBUG                                 10
        logging.INFO                                  20
        logging.WARNING                               30
        logging.ERROR                                 40
        logging.CRITICAL                              50
        """

        logging.Logger.__init__(self, category, log_level)

        # Tries to open the given file. If IOerror occour, send log to stdout
        file_obj = None

        if type(file) == type(sys.stdout):
            # If file is already a file object, just set it to file_obj var
            if 'w' in file.mode or 'a' in file.mode or '+' in file.mode:
                file_obj = file
            else:
                # Without write permission to the given file object,
                # write to stdout
                print _(">>> Given file object in read-only mode! Using "
                        "standard output to write logs!")
                file_obj = sys.stdout
        else:
            try:
                file_obj = open(file, 'a')
            except:
                print _(">>> Couldn't access specified file! Using standard "
                        "output to write logs!")
                file_obj = sys.stdout

        stream_handler = logging.StreamHandler(file_obj)

        # Formater class define a format for the log messages been
        # logged with this handler
        # The following format string
        #   ("%(asctime)s (%(levelname)s) - %(message)s") will result
        # in a log message like this:
        #   2005-09-07 18:15:12,636 (WARNING) - (message!)
        format_string = ("%(asctime)s %(levelname)8s %(filename)s:%(lineno)d "
                         "%(message)s")
        stream_handler.setFormatter(logging.Formatter(format_string,
                                                      datefmt='%F %T'))
        self.addHandler(stream_handler)

    def log(self, message, level=log_level):
        """This method logs messages with default log_level.

        If it's desired another level, user is able to define it using
        the level argument.
        """
        logging.Logger.log(self, level, message)

class Logger:
    log_domain = 'default'
    def __init__(self):
        self.log = Log(category=self.log_domain)

    def debug(self, message):
        self.log.log(level=logging.DEBUG, message=message)

    def info(self, message):
        self.log.log(level=logging.INFO, message=message)

    def error(self, message):
        self.log.log(level=logging.ERROR, message=message)

    def warning(self, message):
        self.log.log(level=logging.WARNING, message=message)

    def critical(self, message):
        self.log.log(level=logging.CRITICAL, message=message)
