# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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

import sys
import unittest

from fiscalprinter.log import Log

class LogTest(unittest.TestCase):
    def setUp(self):
        try:self.log = Log(sys.argv[1])
        except:self.log = Log()
        
    def test_accessible_file(self):
        """Simple test that writes log to an accessible file"""
        print "\n>>> Writing log to accessible file:"
        
        log = Log('/tmp/fiscal_test.log')
        log.log("Testing Log with an accessible file")
        print ">>> Written log:", open('/tmp/fiscal_test.log').readlines()[-1]
        
    def test_stdout(self):
        """Test if Log writes to standard output correctly"""
        print "\n>>> Writing log to standard output:"
                
        log = Log(sys.stdout)
        log.log("Testing Log going to standard output")
        
    def test_stderr(self):
        """Test if Log write to standard error output correctly"""
        print "\n>>> Writing to standard error output:"
        
        log = Log(sys.stderr)
        log.log("Testing Log going to standard error output")
        
    def test_file_without_perm(self):
        """Test Log behavior when user send file without write perms"""
        print "\n>>> Trying to write into file withou write perms:"
                
        log = Log('/etc/shadow')
        log.log("Testing Log with a file without write permissions")
        
    def test_file_read_mode(self):
        """Test Log behavior when user send an file object withou write mode"""
        print "\n>>> Trying to write into file object in read-only mode"
        
        log = Log(open('/tmp/fiscal_test.log'))
        log.log("Testing Log with file object withou write mode")

    def test_debug(self):
        self.log.debug("Debug Message!")
        
    def test_info(self):
        self.log.info("Info Message!")
        
    def test_warning(self):
        self.log.warning("Warning Message!")
        
    def test_error(self):
        self.log.error("Error Message!")
        
    def test_critical(self):
        self.log.critical("Critical Message!")
        
    def test_log(self):
        self.log.log("Default Log Message!")

s = unittest.makeSuite(LogTest)
unittest.TextTestRunner(verbosity=2).run(s)
