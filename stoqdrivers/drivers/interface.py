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
## Author(s):   Johan Dahlin                <jdahlin@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
##
"""
stoqdrivers/drivers/interface.py:
    
    Driver API
"""

class IFiscalPrinterDriver:
    """
    Describes coupon related tasks for a printer.

    Workflow
    
             --<--         --<--                      --<--
            |     |       |     |                    |     |
    open -> add_item ->  add_markup -> totalize -> add_payment -> close

    General argument informations:

        * The 'unit' arguments must be one of the UNIT_* constants
          defined in BaseDriver class.

        * The 'taxcode' arguments must be one of the TAX_* constants
          defined in BaseDriver class.
    """



    #
    # Common API
    #



    def coupon_open(customer, address, document):
        """
        This needs to be called before anything else

        @param customer:
        @type customer:  string
        @param address:
        @type address:  string
        @param document:
        @type document:  string
        """

    def coupon_add_item(code, quantity, price, unit, description, 
                        taxcode, discount, charge):
        """
        Adds an item to the coupon.
        
        @param code:         item code identifier 
        @type  code:         string
        @param quantity:     quantity
        @type  quantity:     number 
        @param price:        price
        @type  price:        number 
        @param unit:         unit specifier
        @type  unit:         a string of length 2
        @param description:  description of product
        @type  desription:   string
        @param taxcode:      constant to descrive the tax
        @type  taxcode:      integer constant one of: TAX_NONE,
                             TAX_SUBSTITUTION, TAX_EXEMPTION
        @param discount:     discount in %
        @type  discount      float 0..100
        @param charge:       charge in % 
        @type  charge        float 0..100

        @rtype:              integer
        @returns             identifier of added item
        """
        
    def coupon_cancel_item(item_id):
        """
        Cancels an item, item_id must be a value returned by
        coupon_add_item
        
        @param item_id:  the item id
        """

    def coupon_cancel():
        """
        Can only be called when a coupon is opened.
        It needs to be possible to open new coupons after this is called.
        """

    def coupon_totalize(discount, charge, taxcode):
        """
        Closes the coupon applies addition a discount or charge and tax
        This can only be called when the coupon is open, has items added
        and payments added.
        
        @param discount:     discount in %
        @type  discount      float 0..100
        @param charge:       charge in % 
        @type  charge        float 0..100
        @param tax_code:     currently unused

        @rtype:              float
        @returns             the coupon total value
        """

    def coupon_add_payment(payment_method, value):
        """
        @param payment_method:    A constant (defined in the constants.py
                                  module) representing the payment method
        @type value:              float
        @param value:             the payment value

        @rtype:                   float
        @returns                  the total remaining amount
        """

    def coupon_close(message=''):
        """
        It needs to be possible to open new coupons after this is called.
        You must call coupon_totalize before calling this method.
        
        @param message:      promotional message
        @type message:       string
        """
    

    #
    # Base admin operations
    #



    def summarize():
        """
        Prints a summary of all sales of the day
        In Brazil this is 'read X' operation
        """

    def close_till():
        """
        Close the till for the day, no other actions can be done
        after this is called
        In Brazil this is 'reduce Z' operation
        """


    #
    # Getting printer status
    #



    def get_status():
        """
        Returns a 3 sized tuple of boolean: Offline, OutOfPaper, Failure
        """
