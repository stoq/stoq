# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# pylint: enable=E1101

import datetime
from decimal import Decimal

from stoqdrivers.enum import TaxType
from storm.expr import Delete

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.runtime import (get_current_station,
                                      get_current_branch,
                                      get_current_user)
from stoqlib.lib.dateutils import localdate, localdatetime, localnow, localtoday
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import validate_cst

# Do not remove, these are used by doctests


def create_branch(store):
    return ExampleCreator.create(store, 'Branch')


class ExampleCreator(object):
    def __init__(self):
        self.clear()

    # Public API

    @classmethod
    def create(cls, store, name):
        ec = cls()
        ec.set_store(store)
        return ec.create_by_type(name)

    def clear(self):
        self._role = None

    def clean_domain(self, domains):
        # The database used for tests is the example one. So, when the tests
        # start, there is already data that could cause unwanted behavior in
        # a few tests, like GUI search ones.
        for domain in domains:
            self.store.execute(Delete(table=domain))

    def set_store(self, store):
        self.store = store

    def create_by_type(self, model_type):
        known_types = {
            'Account': self.create_account,
            'AccountTransaction': self.create_account_transaction,
            'Address': self.create_address,
            'BankAccount': self.create_bank_account,
            'Branch': self.create_branch,
            'BranchStation': self.get_station,
            'Calls': self.create_call,
            'CfopData': self.create_cfop_data,
            'CityLocation': self.get_location,
            'Client': self.create_client,
            'ClientCategory': self.create_client_category,
            'ClientCategoryPrice': self.create_client_category_price,
            'Company': self.create_company,
            'CostCenter': self.create_cost_center,
            'CreditCheckHistory': self.create_credit_check_history,
            'CreditProvider': self.create_credit_provider,
            'Delivery': self.create_delivery,
            'Employee': self.create_employee,
            'EmployeeRole': self.create_employee_role,
            'FiscalBookEntry': self.create_fiscal_book_entry,
            'FiscalDayHistory': self.create_fiscal_day_history,
            'Image': self.create_image,
            'Individual': self.create_individual,
            'Inventory': self.create_inventory,
            'InventoryItem': self.create_inventory_item,
            'InvoicePrinter': self.create_invoice_printer,
            'Loan': self.create_loan,
            'LoanItem': self.create_loan_item,
            'LoginUser': self.create_user,
            'MilitaryData': self.create_military_data,
            'ParameterData': self.create_parameter_data,
            'Payment': self.create_payment,
            'PaymentCategory': self.create_payment_category,
            'PaymentGroup': self.create_payment_group,
            'PaymentMethod': self.get_payment_method,
            'PaymentRenegotiation': self.create_payment_renegotiation,
            'Person': self.create_person,
            'Product': self.create_product,
            'ProductManufacturer': self.create_product_manufacturer,
            'ProductSupplierInfo': self.create_product_supplier_info,
            'ProductionItem': self.create_production_item,
            'ProductionMaterial': self.create_production_material,
            'ProductionOrder': self.create_production_order,
            'ProductionService': self.create_production_service,
            'PurchaseItem': self.create_purchase_order_item,
            'PurchaseOrder': self.create_purchase_order,
            'Quotation': self.create_quotation,
            'QuoteGroup': self.create_quote_group,
            'ReceivingOrder': self.create_receiving_order,
            'ReceivingOrderItem': self.create_receiving_order_item,
            'ReturnedSale': self.create_returned_sale,
            'Sale': self.create_sale,
            'SaleItem': self.create_sale_item,
            'InvoiceItemIcms': self.create_invoice_item_icms,
            'InvoiceItemIpi': self.create_invoice_item_ipi,
            'SalesPerson': self.create_sales_person,
            'Sellable': self.create_sellable,
            'SellableCategory': self.create_sellable_category,
            'SellableTaxConstant': self.create_sellable_tax_constant,
            'SellableUnit': self.create_sellable_unit,
            'Service': self.create_service,
            'StockDecrease': self.create_stock_decrease,
            'StockDecreaseItem': self.create_stock_decrease_item,
            'Storable': self.create_storable,
            'Supplier': self.create_supplier,
            'Till': self.create_till,
            'TransferOrder': self.create_transfer,
            'Transporter': self.create_transporter,
            'UserProfile': self.create_user_profile,
            'VoterData': self.create_voter_data,
            'WorkOrder': self.create_workorder,
            'WorkOrderPackage': self.create_workorder_package,
            'WorkPermitData': self.create_work_permit_data,
        }
        if isinstance(model_type, basestring):
            model_name = model_type
        else:
            model_name = model_type.__name__
        if model_name in known_types:
            return known_types[model_name]()

    def create_person(self, name=u'John'):
        from stoqlib.domain.person import Person
        return Person(name=name, store=self.store)

    def create_branch(self, name=u'Dummy', phone_number=u'12345678',
                      fax_number=u'87564321', person=None, crt=1):
        from stoqlib.domain.person import Branch, Company, Person
        if person is None:
            person = Person(name=name, phone_number=phone_number,
                            fax_number=fax_number, store=self.store)
            self.create_address(person=person)
            fancy_name = name + u' shop'
            Company(person=person, fancy_name=fancy_name,
                    store=self.store)
        return Branch(person=person, store=self.store, crt=crt)

    def create_supplier(self, name=u'Supplier', fancy_name=u'Company Name',
                        person=None):
        from stoqlib.domain.person import Company, Person, Supplier
        if person is None:
            person = Person(name=name, store=self.store)
            Company(person=person, fancy_name=fancy_name,
                    cnpj=u'90.117.749/7654-80',
                    store=self.store)
        return Supplier(person=person, store=self.store)

    def create_transporter(self, name=u'John', person=None):
        from stoqlib.domain.person import Company, Transporter
        if person is None:
            person = self.create_person(name)
            Company(person=person, store=self.store)
        return Transporter(person=person, store=self.store)

    def create_employee_role(self, name=u'Role'):
        from stoqlib.domain.person import EmployeeRole
        role = self.store.find(EmployeeRole, name=name).one()
        if not role:
            role = EmployeeRole(name=name, store=self.store)
        if not self._role:
            self._role = role
        return role

    def create_employee(self, name=u"SalesPerson", person=None):
        from stoqlib.domain.person import Employee, Individual, Person
        if person is None:
            person = Person(name=name, store=self.store)
            Individual(person=person, store=self.store)
        return Employee(person=person,
                        role=self.create_employee_role(),
                        store=self.store)

    def create_sales_person(self, person=None, name=u'SalesPerson'):
        from stoqlib.domain.person import SalesPerson
        if person is None:
            employee = self.create_employee(name=name)
            person = employee.person
        return SalesPerson(person=person, store=self.store)

    def create_client(self, name=u'Client', person=None):
        from stoqlib.domain.person import Client, Individual, Person
        if person is None:
            person = Person(name=name, store=self.store)
            Individual(person=person, store=self.store)
        return Client(person=person, store=self.store)

    def create_individual(self, person=None):
        from stoqlib.domain.person import Individual, Person
        if person is None:
            person = Person(name=u'individual', store=self.store)
        return Individual(person=person,
                          birth_date=localdatetime(1970, 1, 1),
                          store=self.store)

    def create_company(self, person=None):
        from stoqlib.domain.person import Company, Person
        if person is None:
            person = Person(name=u'Dummy', store=self.store)
        return Company(person=person, fancy_name=u'Dummy shop',
                       store=self.store)

    def create_user(self, username=u'username', person=None):
        from stoqlib.domain.person import LoginUser
        if person is None:
            individual = self.create_individual()
            person = individual.person

        profile = self.create_user_profile()
        # FIXME: Some tests are calling this twice without passing different
        # usernames. Remove this line and fix them directly
        while not self.store.find(LoginUser, username=username).is_empty():
            username += u'1'

        return LoginUser(person=person,
                         username=username,
                         password=u'password',
                         profile=profile,
                         store=self.store)

    def create_storable(self, product=None, branch=None, stock=0,
                        unit_cost=None, is_batch=False):
        from stoqlib.domain.product import Storable, StockTransactionHistory
        if not product:
            sellable = self.create_sellable()
            product = sellable.product
        storable = Storable(product=product, store=self.store, is_batch=is_batch)
        if branch and stock:
            batch = self.create_storable_batch(storable) if is_batch else None
            storable.increase_stock(
                stock, branch,
                type=StockTransactionHistory.TYPE_INITIAL,
                object_id=None,
                unit_cost=unit_cost,
                batch=batch)
            if is_batch:
                return storable, batch
        return storable

    def create_storable_batch(self, storable=None, batch_number=u'1'):
        from stoqlib.domain.product import StorableBatch
        if not storable:
            storable = self.create_storable()
        return StorableBatch(store=self.store, storable=storable,
                             batch_number=batch_number)

    def create_product_stock_item(self, stock_cost=0, quantity=0,
                                  branch=None, storable=None):
        sth = self.create_stock_transaction_history(
            storable=storable, branch=branch, quantity=quantity,
            stock_cost=stock_cost)
        return sth.product_stock_item

    def create_stock_transaction_history(self, storable=None, branch=None,
                                         batch=None, stock_cost=0, quantity=0,
                                         trans_type=None):
        from stoqlib.domain.product import StockTransactionHistory
        trans_type = trans_type or StockTransactionHistory.TYPE_INITIAL
        branch = branch or get_current_branch(store=self.store)
        storable = storable or self.create_storable()
        sth = StockTransactionHistory(
            branch=branch,
            storable=storable,
            batch=batch,
            responsible=get_current_user(store=self.store),
            unit_cost=stock_cost,
            quantity=quantity,
            type=trans_type,
            store=self.store)
        return sth

    def create_product_supplier_info(self, supplier=None, product=None):
        from stoqlib.domain.product import ProductSupplierInfo
        product = product or self.create_product(with_supplier=False)
        supplier = supplier or self.create_supplier()
        return ProductSupplierInfo(
            store=self.store,
            supplier=supplier,
            product=product,
            is_main_supplier=True,
        )

    def create_product(self, price=None, with_supplier=True,
                       branch=None, stock=None, storable=False, code=u'',
                       description=u'Description', is_grid=False, parent=None,
                       is_package=False):
        from stoqlib.domain.product import Storable, StockTransactionHistory
        sellable = self.create_sellable(price=price, code=code,
                                        description=description)
        if with_supplier:
            self.create_product_supplier_info(product=sellable.product)
        if is_package:
            # Package product should not have stock nor storable
            assert not stock and not storable

        product = sellable.product
        product.parent = parent
        if not branch:
            branch = get_current_branch(self.store)
        if storable or stock:
            storable = Storable(product=product, store=self.store)
        if stock:
            storable.increase_stock(stock, branch,
                                    type=StockTransactionHistory.TYPE_INITIAL,
                                    object_id=None,
                                    unit_cost=10)
        product.is_grid = is_grid
        if is_grid or is_package:
            product.manage_stock = False

        product.is_package = is_package

        return product

    def create_attribute_group(self, description=None):
        from stoqlib.domain.product import GridGroup
        if not description:
            description = u'grid group 1'
        return GridGroup(store=self.store, description=description)

    def create_grid_attribute(self, attribute_group=None, description=None):
        from stoqlib.domain.product import GridAttribute
        if not attribute_group:
            attribute_group = self.create_attribute_group()
        if not description:
            description = u'grid attribute 1'

        return GridAttribute(store=self.store, description=description,
                             group_id=attribute_group.id)

    def create_attribute_option(self, grid_attribute=None, description=None,
                                order=None):
        from stoqlib.domain.product import GridOption
        if not grid_attribute:
            grid_attribute = self.create_grid_attribute()
        if not description:
            description = u'grid option 1'

        return GridOption(store=self.store, description=description,
                          attribute_id=grid_attribute.id,
                          option_order=order or 1)

    def create_product_attribute(self, product=None, attribute=None):
        from stoqlib.domain.product import ProductAttribute
        if not product:
            product = self.create_product(is_grid=True)
        if not attribute:
            attribute = self.create_grid_attribute()
            self.create_attribute_option(attribute)

        return ProductAttribute(store=self.store, product_id=product.id,
                                attribute_id=attribute.id)

    def create_product_manufacturer(self, name=u'', code=u''):
        from stoqlib.domain.product import ProductManufacturer

        return ProductManufacturer(store=self.store, name=name, code=code)

    def create_product_component(self, product=None, component=None,
                                 component_quantity=1, price=0, storable=False):
        from stoqlib.domain.product import ProductComponent
        return ProductComponent(store=self.store,
                                product=product or self.create_product(storable=storable),
                                component=component or self.create_product(storable=storable),
                                quantity=component_quantity,
                                price=price)

    def create_sellable(self, price=None, product=True,
                        description=u'Description', code=u'', storable=False):
        from stoqlib.domain.product import Product, Storable
        from stoqlib.domain.service import Service
        from stoqlib.domain.sellable import Sellable
        tax_constant_id = sysparam.get_object_id('DEFAULT_PRODUCT_TAX_CONSTANT')
        if price is None:
            price = 10
        sellable = Sellable(cost=125,
                            price=price,
                            description=description,
                            store=self.store)
        sellable.code = code
        sellable.tax_constant_id = tax_constant_id
        if product:
            p = Product(sellable=sellable, store=self.store)
            if storable:
                Storable(product=p, store=self.store)
        else:
            Service(sellable=sellable, store=self.store)
        return sellable

    def create_sellable_unit(self, description=u'', allow_fraction=True):
        from stoqlib.domain.sellable import SellableUnit
        return SellableUnit(store=self.store,
                            description=description,
                            allow_fraction=allow_fraction)

    def create_sellable_category(self, description=None, parent=None):
        from stoqlib.domain.sellable import SellableCategory
        description = description or u"Category"
        return SellableCategory(description=description,
                                category=parent,
                                store=self.store)

    def create_sale(self, branch=None, client=None, sale_token=None,
                    salesperson=None):
        from stoqlib.domain.sale import Sale, SaleToken
        from stoqlib.domain.till import Till
        till = Till.get_current(self.store)
        if till is None:
            till = self.create_till()
            till.open_till()
        group = self.create_payment_group()
        if client:
            group.payer = client.person

        if sale_token:
            sale_token.status = SaleToken.STATUS_OCCUPIED

        sale = Sale(store=self.store,
                    coupon_id=0,
                    open_date=TransactionTimestamp(),
                    salesperson=salesperson or self.create_sales_person(),
                    branch=branch or get_current_branch(self.store),
                    cfop_id=sysparam.get_object_id('DEFAULT_SALES_CFOP'),
                    group=group,
                    client=client,
                    sale_token=sale_token)
        return sale

    def create_sale_token(self, code=u''):
        from stoqlib.domain.sale import SaleToken
        return SaleToken(store=self.store,
                         status=SaleToken.STATUS_AVAILABLE,
                         code=code)

    def create_sale_comment(self, sale, comment=u'Foo bar', user=None):
        from stoqlib.domain.sale import SaleComment
        return SaleComment(store=self.store, sale=sale, comment=comment,
                           author=user or get_current_user(self.store))

    def create_trade(self, trade_value=100):
        from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
        branch = get_current_branch(self.store)
        returned_sale = ReturnedSale(store=self.store,
                                     responsible=get_current_user(self.store),
                                     branch=branch)
        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=trade_value,
                         sellable=self.create_sellable(),
                         returned_sale=returned_sale)

        new_sale = self.create_sale()
        product_price = trade_value * 2
        self.add_product(new_sale, price=product_price)
        new_sale.discount_value = trade_value
        returned_sale.new_sale = new_sale
        return returned_sale

    def create_returned_sale(self, sale=None):
        if not sale:
            sale = self.create_sale()
        return sale.create_sale_return_adapter()

    def create_pending_returned_sale(self, product=None):
        from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
        sale_branch = get_current_branch(self.store)
        return_branch = self.create_branch()
        client = self.create_client()
        product = product or self.create_product()
        sale = self.create_sale(branch=sale_branch, client=client)
        sale_item = sale.add_sellable(sellable=product.sellable)

        r_sale = ReturnedSale(store=self.store,
                              sale=sale,
                              branch=return_branch,
                              responsible=get_current_user(self.store))

        ReturnedSaleItem(store=self.store,
                         quantity=1,
                         price=100,
                         sale_item=sale_item,
                         returned_sale=r_sale,
                         sellable=sale_item.sellable)
        return r_sale

    def create_returned_sale_item(self, returned_sale=None, sale_item=None,
                                  parent_item=None):
        from stoqlib.domain.returnedsale import ReturnedSaleItem
        sale_item = sale_item or self.create_sale_item()
        returned_sale = returned_sale or self.create_returned_sale()
        return ReturnedSaleItem(store=self.store,
                                quantity=1,
                                price=100,
                                sale_item=sale_item,
                                returned_sale=returned_sale,
                                sellable=sale_item.sellable,
                                parent_item=parent_item)

    def create_sale_item(self, sale=None, product=True, quantity=1,
                         sellable=None, parent_item=None):
        from stoqlib.domain.sale import SaleItem
        sellable = sellable or self.create_sellable(product=product)
        return SaleItem(store=self.store,
                        quantity=quantity,
                        price=100,
                        sale=sale or self.create_sale(),
                        sellable=sellable,
                        parent_item=parent_item)

    def create_product_tax_template(self, name=u'Tax template', tax_type=None):
        from stoqlib.domain.taxes import ProductTaxTemplate
        if tax_type is None:
            tax_type = ProductTaxTemplate.TYPE_ICMS
        return ProductTaxTemplate(store=self.store, name=name, tax_type=tax_type)

    def create_product_icms_template(self, tax_template=None, crt=1, orig=0,
                                     code=0, mod_bc=0, p_icms=0, p_icms_st=0,
                                     p_mva_st=0, p_red_bc_st=0, p_cred_sn=None,
                                     mod_bc_st=None, v_icms=None):
        from stoqlib.domain.taxes import ProductIcmsTemplate
        if tax_template is None:
            tax_template = self.create_product_tax_template()
        # Simples nacional
        if crt in [1, 2]:
            return ProductIcmsTemplate(store=self.store,
                                       product_tax_template=tax_template,
                                       orig=orig, csosn=code, mod_bc=mod_bc,
                                       p_icms=p_icms, p_icms_st=p_icms_st,
                                       p_mva_st=p_mva_st,
                                       p_red_bc_st=p_red_bc_st,
                                       mod_bc_st=mod_bc_st,
                                       p_cred_sn=p_cred_sn)
        # Regime normal
        return ProductIcmsTemplate(store=self.store,
                                   product_tax_template=tax_template,
                                   orig=orig,
                                   cst=code, mod_bc=mod_bc,
                                   p_icms=p_icms,
                                   p_icms_st=p_icms_st,
                                   p_mva_st=p_mva_st,
                                   p_red_bc_st=p_red_bc_st,
                                   mod_bc_st=mod_bc_st)

    def create_product_ipi_template(self, tax_template=None, cl_enq=u'000',
                                    cnpj_prod=u'00.000.000/0001-00',
                                    c_selo=u'000', q_selo=1, c_enq=u'000', cst=0, p_ipi=0,
                                    q_unid=0, calculo=None):
        from stoqlib.domain.taxes import (ProductIpiTemplate,
                                          ProductTaxTemplate)
        if calculo is None:
            calculo = ProductIpiTemplate.CALC_ALIQUOTA
        if tax_template is None:
            ipi_tax = ProductTaxTemplate.TYPE_IPI
            tax_template = self.create_product_tax_template(tax_type=ipi_tax)

        return ProductIpiTemplate(store=self.store,
                                  product_tax_template=tax_template,
                                  cl_enq=cl_enq, cnpj_prod=cnpj_prod,
                                  c_selo=c_selo, q_selo=q_selo, c_enq=c_enq,
                                  cst=cst, p_ipi=p_ipi, q_unid=q_unid,
                                  calculo=calculo)

    def create_product_pis_template(self, tax_template=None, cst=1,
                                    p_pis=0, calculo=None):
        from stoqlib.domain.taxes import (ProductPisTemplate,
                                          ProductTaxTemplate)

        assert validate_cst(cst)
        if calculo is None:
            calculo = ProductPisTemplate.CALC_PERCENTAGE
        if tax_template is None:
            pis_tax = ProductTaxTemplate.TYPE_PIS
            tax_template = self.create_product_tax_template(tax_type=pis_tax)
        return ProductPisTemplate(product_tax_template=tax_template,
                                  cst=cst, p_pis=p_pis,
                                  calculo=calculo)

    def create_product_cofins_template(self, tax_template=None, cst=1,
                                       p_cofins=0, calculo=None):
        from stoqlib.domain.taxes import (ProductCofinsTemplate,
                                          ProductTaxTemplate)

        assert validate_cst(cst)
        if calculo is None:
            calculo = ProductCofinsTemplate.CALC_PERCENTAGE
        if tax_template is None:
            cofins_tax = ProductTaxTemplate.TYPE_COFINS
            tax_template = self.create_product_tax_template(tax_type=cofins_tax)
        return ProductCofinsTemplate(product_tax_template=tax_template,
                                     cst=cst, p_cofins=p_cofins,
                                     calculo=calculo)

    def create_invoice_item_icms(self):
        from stoqlib.domain.taxes import InvoiceItemIcms
        return InvoiceItemIcms(store=self.store)

    def create_invoice_item_ipi(self):
        from stoqlib.domain.taxes import InvoiceItemIpi
        return InvoiceItemIpi(store=self.store)

    def create_invoice_item_pis(self, v_pis=0, v_bc=None, p_pis=None,
                                q_bc_prod=None, cst=None, calculo=None):
        from stoqlib.domain.taxes import InvoiceItemPis
        assert validate_cst(cst)
        if calculo is None:
            calculo = InvoiceItemPis.CALC_PERCENTAGE

        return InvoiceItemPis(store=self.store, v_pis=v_pis, v_bc=v_bc,
                              p_pis=p_pis, q_bc_prod=q_bc_prod,
                              cst=cst, calculo=calculo)

    def create_invoice_item_cofins(self, v_cofins=0, v_bc=None,
                                   p_cofins=None, q_bc_prod=None,
                                   cst=None, calculo=None):
        from stoqlib.domain.taxes import InvoiceItemCofins
        assert validate_cst(cst)
        if calculo is None:
            calculo = InvoiceItemCofins.CALC_PERCENTAGE

        return InvoiceItemCofins(store=self.store, v_cofins=v_cofins, v_bc=v_bc,
                                 p_cofins=p_cofins, q_bc_prod=q_bc_prod,
                                 cst=cst, calculo=calculo)

    def create_invoice_layout(self):
        from stoqlib.domain.invoice import InvoiceLayout
        return InvoiceLayout(store=self.store, description=u'Untitled',
                             width=80, height=40)

    def create_invoice_field(self, field_name=None, layout=None, content=u''):
        from stoqlib.domain.invoice import InvoiceField
        return InvoiceField(store=self.store, layout=layout,
                            field_name=field_name,
                            x=0, y=0, width=10, height=1, content=content)

    def create_client_category(self, name=u'Category 1'):
        from stoqlib.domain.person import ClientCategory
        return ClientCategory(name=name, store=self.store)

    def create_client_category_price(self, category=None, sellable=None,
                                     price=None):
        from stoqlib.domain.sellable import ClientCategoryPrice
        return ClientCategoryPrice(sellable=sellable or self.create_sellable(price=50),
                                   category=category or self.create_client_category(),
                                   price=price or 100,
                                   store=self.store)

    def create_stock_decrease_item(self, stock_decrease=None, quantity=1,
                                   sellable=None, cost=100):
        from stoqlib.domain.stockdecrease import StockDecreaseItem
        return StockDecreaseItem(stock_decrease=stock_decrease or self.create_stock_decrease(),
                                 sellable=sellable or self.create_sellable(),
                                 quantity=quantity,
                                 cost=cost,
                                 store=self.store)

    def create_stock_decrease(self, branch=None, user=None, reason=u'', group=None,
                              destination=None):
        from stoqlib.domain.stockdecrease import StockDecrease

        employee = self.create_employee()
        cfop = self.create_cfop_data()
        return StockDecrease(responsible=user or get_current_user(self.store),
                             removed_by=employee,
                             branch=branch or get_current_branch(self.store),
                             person=destination or self.create_person(),
                             status=StockDecrease.STATUS_INITIAL,
                             cfop=cfop,
                             reason=reason,
                             invoice_number=1337,
                             group=group,
                             store=self.store)

    def create_city_location(self, city=None, state=None, country=None):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_or_create(
            self.store,
            country=country or u'United States',
            city=city or u'Los Angeles',
            state=state or u'Californa',
        )

    def create_address(self, person=None, city_location=None):
        from stoqlib.domain.address import Address
        city_location = city_location or self.create_city_location()
        return Address(street=u'Mainstreet',
                       streetnumber=138,
                       district=u'Cidade Araci',
                       postal_code=u'12345-678',
                       complement=u'Compl',
                       is_main_address=True,
                       person=person,
                       city_location=city_location,
                       store=self.store)

    def create_parameter_data(self):
        from stoqlib.domain.parameter import ParameterData
        return self.store.find(ParameterData)[0]

    def create_till(self):
        from stoqlib.domain.till import Till
        station = get_current_station(self.store)
        return Till(store=self.store, station=station)

    def create_user_profile(self, name=None, max_discount=None):
        from stoqlib.domain.profile import UserProfile
        return UserProfile(store=self.store,
                           name=name or u'assistant',
                           max_discount=max_discount or 0)

    def create_profile_settings(self, user_profile=None, app=u'admin'):
        from stoqlib.domain.profile import ProfileSettings
        return ProfileSettings(store=self.store, app_dir_name=app,
                               has_permission=True,
                               user_profile=user_profile)

    def create_purchase_order(self, supplier=None, branch=None):
        from stoqlib.domain.purchase import PurchaseOrder
        group = self.create_payment_group()
        return PurchaseOrder(supplier=supplier or self.create_supplier(),
                             branch=branch or self.create_branch(),
                             group=group,
                             responsible=get_current_user(self.store),
                             store=self.store)

    def create_quote_group(self, branch=None):
        from stoqlib.domain.purchase import QuoteGroup
        if not branch:
            branch = get_current_branch(self.store)
        return QuoteGroup(store=self.store, branch=branch)

    def create_quotation(self):
        from stoqlib.domain.purchase import Quotation
        purchase_order = self.create_purchase_order()
        quote_group = self.create_quote_group(branch=purchase_order.branch)
        return Quotation(store=self.store,
                         group=quote_group,
                         purchase=purchase_order,
                         branch=purchase_order.branch)

    def create_purchase_order_item(self, order=None, cost=125, sellable=None,
                                   parent_item=None):
        if not order:
            order = self.create_purchase_order()
        from stoqlib.domain.purchase import PurchaseItem
        return PurchaseItem(store=self.store,
                            quantity=8, quantity_received=0,
                            cost=cost, base_cost=125,
                            sellable=sellable or self.create_sellable(),
                            order=order,
                            parent_item=parent_item)

    def create_production_order(self, branch=None):
        if branch is None:
            branch = get_current_branch(self.store)
        from stoqlib.domain.production import ProductionOrder
        return ProductionOrder(branch=branch,
                               responsible=self.create_employee(),
                               description=u'production',
                               store=self.store)

    def create_production_item(self, quantity=1, order=None, storable=True):
        from stoqlib.domain.product import ProductComponent, Storable
        from stoqlib.domain.production import (ProductionItem,
                                               ProductionMaterial)
        product = self.create_product(10)
        Storable(product=product, store=self.store)
        component = self.create_product(5)
        if storable:
            Storable(product=component, store=self.store)
        ProductComponent(product=product,
                         component=component,
                         store=self.store)

        if not order:
            order = self.create_production_order()
        component = list(product.get_components())[0]
        ProductionMaterial(product=component.component,
                           order=order,
                           needed=quantity,
                           store=self.store)

        return ProductionItem(product=product,
                              order=order,
                              quantity=quantity,
                              store=self.store)

    def create_production_material(self):
        from stoqlib.domain.production import ProductionMaterial
        production_item = self.create_production_item()
        order = production_item.order
        component = list(production_item.get_components())[0]
        return self.store.find(ProductionMaterial, product=component.component,
                               order=order).one()

    def create_production_service(self):
        from stoqlib.domain.production import ProductionService
        service = self.create_service()
        return ProductionService(service=service,
                                 order=self.create_production_order(),
                                 store=self.store)

    def create_cfop_data(self, code=u'123'):
        from stoqlib.domain.fiscal import CfopData
        return CfopData(store=self.store, code=code,
                        description=u'test')

    def create_receiving_order(self, purchase_order=None, branch=None, user=None):
        from stoqlib.domain.receiving import ReceivingOrder
        if purchase_order is None:
            purchase_order = self.create_purchase_order()
        cfop = self.create_cfop_data()
        cfop.code = u'1.102'
        receiving = ReceivingOrder(store=self.store,
                                   invoice_number=222,
                                   supplier=purchase_order.supplier,
                                   responsible=user or get_current_user(self.store),
                                   branch=branch or get_current_branch(self.store),
                                   cfop=cfop)
        receiving.add_purchase(purchase_order)
        return receiving

    def create_receiving_order_item(self, receiving_order=None, sellable=None,
                                    purchase_item=None, quantity=8,
                                    parent_item=None):
        from stoqlib.domain.receiving import ReceivingOrderItem
        from stoqlib.domain.product import Storable
        if receiving_order is None:
            receiving_order = self.create_receiving_order()
        if sellable is None:
            sellable = self.create_sellable()
            product = sellable.product
            Storable(product=product, store=self.store)
        if purchase_item is None:
            purchase_item = receiving_order.purchase_orders.find()[0].add_item(
                sellable, quantity)
        return ReceivingOrderItem(store=self.store,
                                  quantity=quantity, cost=125,
                                  purchase_item=purchase_item,
                                  sellable=sellable,
                                  receiving_order=receiving_order,
                                  parent_item=parent_item)

    def create_fiscal_book_entry(self, entry_type=None, icms_value=0,
                                 iss_value=0, ipi_value=0,
                                 invoice_number=None):
        from stoqlib.domain.payment.group import PaymentGroup
        from stoqlib.domain.fiscal import FiscalBookEntry
        payment_group = PaymentGroup(store=self.store)
        return FiscalBookEntry(invoice_number=invoice_number,
                               icms_value=icms_value,
                               iss_value=iss_value,
                               ipi_value=ipi_value,
                               entry_type=entry_type,
                               cfop=self.create_cfop_data(),
                               branch=self.create_branch(),
                               drawee=self.create_person(),
                               payment_group=payment_group,
                               store=self.store)

    def create_icms_ipi_book_entry(self):
        from stoqlib.domain.fiscal import FiscalBookEntry
        return self.create_fiscal_book_entry(FiscalBookEntry.TYPE_PRODUCT,
                                             icms_value=10, ipi_value=10,
                                             invoice_number=200)

    def create_iss_book_entry(self):
        from stoqlib.domain.fiscal import FiscalBookEntry
        return self.create_fiscal_book_entry(FiscalBookEntry.TYPE_SERVICE,
                                             iss_value=10,
                                             invoice_number=201)

    def create_service(self, description=u'Description', price=10):
        from stoqlib.domain.sellable import Sellable, SellableTaxConstant
        from stoqlib.domain.service import Service
        tax_constant = SellableTaxConstant.get_by_type(
            TaxType.SERVICE, self.store)
        sellable = Sellable(price=price,
                            description=description,
                            store=self.store)
        sellable.tax_constant = tax_constant
        service = Service(sellable=sellable, store=self.store)
        return service

    def create_bank_account(self, account=None):
        from stoqlib.domain.account import BankAccount
        return BankAccount(store=self.store,
                           bank_branch=u'2666-1',
                           bank_account=u'20.666-1',
                           bank_number=1,
                           account=account or self.create_account())

    def create_credit_provider(self, short_name=u'Velec'):
        from stoqlib.domain.payment.card import CreditProvider
        return CreditProvider(store=self.store,
                              short_name=short_name,
                              open_contract_date=localdate(2006, 01, 01))

    def create_card_device(self, description=u'Cielo'):
        from stoqlib.domain.payment.card import CardPaymentDevice
        return CardPaymentDevice(store=self.store,
                                 description=description)

    def create_operation_cost(self, device=None, provider=None, card_type=None,
                              start=1, end=1):
        from stoqlib.domain.payment.card import CardOperationCost, CreditCardData
        if card_type is None:
            card_type = CreditCardData.TYPE_CREDIT
        return CardOperationCost(store=self.store,
                                 device=device or self.create_card_device(),
                                 provider=provider or self.create_credit_provider(),
                                 card_type=card_type,
                                 installment_start=start,
                                 installment_end=end)

    def create_payment(self, payment_type=None, date=None, value=None,
                       method=None, branch=None, group=None):
        from stoqlib.domain.payment.payment import Payment
        if payment_type is None:
            payment_type = Payment.TYPE_OUT
        if not date:
            date = localtoday()
        return Payment(group=group or self.create_payment_group(),
                       description=u'Test payment',
                       branch=branch or get_current_branch(self.store),
                       open_date=date,
                       due_date=date,
                       value=Decimal(value or 10),
                       method=method or self.get_payment_method(),
                       category=None,
                       store=self.store,
                       payment_type=payment_type)

    def create_card_payment(self, date=None, provider_id=u'AMEX', device=None,
                            payment_value=None, payment_type=None):
        from stoqlib.domain.payment.card import CreditCardData, CreditProvider
        if date is None:
            date = localnow()

        provider = self.store.find(CreditProvider, provider_id=provider_id).one()

        payment = self.create_payment(date=date,
                                      method=self.get_payment_method(u'card'),
                                      payment_type=payment_type,
                                      value=payment_value)

        CreditCardData(payment=payment, provider=provider,
                       device=device or self.create_card_device(),
                       store=self.store)

        return payment

    def create_credit_card_data(self, provider=None, device=None,
                                payment_type=None, payment_value=None):
        from stoqlib.domain.payment.card import CreditCardData
        payment = self.create_card_payment(date=None,
                                           provider_id=provider.provider_id,
                                           device=device,
                                           payment_type=payment_type,
                                           payment_value=payment_value)

        return self.store.find(CreditCardData, payment_id=payment.id).one()

    def create_payment_group(self, payer=None):
        from stoqlib.domain.payment.group import PaymentGroup
        return PaymentGroup(store=self.store, payer=payer)

    def create_payment_comment(self, comment):
        from stoqlib.domain.payment.comment import PaymentComment
        return PaymentComment(store=self.store, comment=comment)

    def create_sellable_tax_constant(self):
        from stoqlib.domain.sellable import SellableTaxConstant
        return SellableTaxConstant(description=u"18",
                                   tax_type=int(TaxType.CUSTOM),
                                   tax_value=18,
                                   store=self.store)

    def create_station(self, branch=None):
        if branch is None:
            branch = get_current_branch(self.store)
        from stoqlib.domain.station import BranchStation
        return BranchStation(name=u"station",
                             branch=branch,
                             store=self.store)

    def create_transfer_order(self, source_branch=None, dest_branch=None):
        from stoqlib.domain.transfer import TransferOrder
        source_branch = source_branch or self.create_branch(u"Source")
        dest_branch = dest_branch or self.create_branch(u"Dest")
        source_resp = self.create_employee(u"Ipswich")
        dest_resp = self.create_employee(u"Bolton")
        return TransferOrder(source_branch=source_branch,
                             destination_branch=dest_branch,
                             source_responsible=source_resp,
                             destination_responsible=dest_resp,
                             store=self.store)

    def create_transfer_order_item(self, order=None, quantity=5, sellable=None,
                                   batch=None, stock_cost=50):
        from stoqlib.domain.product import Product, Storable, StockTransactionHistory
        if not order:
            order = self.create_transfer_order()
        if not sellable:
            sellable = self.create_sellable()
        product = self.store.find(Product, sellable=sellable).one()
        if not product.storable:
            storable = Storable(product=product, store=self.store)
            storable.increase_stock(quantity, order.source_branch,
                                    type=StockTransactionHistory.TYPE_TRANSFER_FROM,
                                    unit_cost=stock_cost,
                                    object_id=None)
        return order.add_sellable(sellable, batch=batch, quantity=quantity)

    # FIXME: Rename to create_work_order
    def create_workorder(self, sellable=None, description=u'',
                         branch=None, current_branch=None, client=None):
        from stoqlib.domain.workorder import WorkOrder
        return WorkOrder(
            store=self.store,
            sellable=sellable or self.create_sellable(),
            description=description,
            client=client or self.create_client(),
            branch=branch or get_current_branch(self.store),
            current_branch=current_branch)

    def create_work_order_item(self, quantity=1, price=10, order=None):
        if not order:
            order = self.create_workorder()
        from stoqlib.domain.workorder import WorkOrderItem
        sellable = self.create_sellable()
        return WorkOrderItem(
            store=self.store,
            order=order,
            quantity=quantity,
            price=price,
            sellable=sellable)

    # FIXME: Rename to create_work_order_package
    def create_workorder_package(self, identifier=u'', source_branch=None):
        from stoqlib.domain.workorder import WorkOrderPackage
        return WorkOrderPackage(
            store=self.store,
            source_branch=source_branch or get_current_branch(self.store),
            identifier=identifier)

    def create_inventory(self, branch=None):
        from stoqlib.domain.inventory import Inventory
        branch = branch or self.create_branch(u"Main")
        responsible = self.create_user()
        return Inventory(store=self.store,
                         branch=branch, responsible=responsible)

    def create_inventory_item(self, inventory=None, quantity=5, product=None):
        from stoqlib.domain.inventory import InventoryItem
        from stoqlib.domain.product import Storable, StockTransactionHistory
        if not inventory:
            inventory = self.create_inventory()
        sellable = self.create_sellable()
        if product is None:
            product = sellable.product
            storable = Storable(product=product, store=self.store)
            storable.increase_stock(quantity, inventory.branch,
                                    type=StockTransactionHistory.TYPE_INITIAL,
                                    object_id=None)
        return InventoryItem(product=product,
                             product_cost=product.sellable.cost,
                             recorded_quantity=quantity,
                             inventory=inventory,
                             store=self.store)

    def create_loan(self, branch=None, client=None):
        from stoqlib.domain.loan import Loan
        user = get_current_user(self.store)
        return Loan(responsible=user,
                    client=client,
                    branch=branch or get_current_branch(self.store),
                    store=self.store)

    def create_loan_item(self, loan=None, quantity=1):
        from stoqlib.domain.loan import LoanItem
        from stoqlib.domain.product import Storable, StockTransactionHistory
        loan = loan or self.create_loan()
        sellable = self.create_sellable()
        storable = Storable(product=sellable.product,
                            store=self.store)
        storable.increase_stock(10, loan.branch,
                                type=StockTransactionHistory.TYPE_INITIAL,
                                object_id=None)
        return LoanItem(loan=loan, sellable=sellable, price=10, base_price=10,
                        quantity=quantity, store=self.store)

    def get_payment_method(self, name=u'money'):
        from stoqlib.domain.payment.method import PaymentMethod
        return PaymentMethod.get_by_name(self.store, name)

    def get_station(self):
        return get_current_station(self.store)

    def get_location(self):
        from stoqlib.domain.address import CityLocation
        return CityLocation.get_default(self.store)

    def add_product(self, sale, price=None, quantity=1, code=u''):
        from stoqlib.domain.product import Storable, StockTransactionHistory
        product = self.create_product(price=price, code=code)
        sellable = product.sellable
        sellable.tax_constant = self.create_sellable_tax_constant()
        sale.add_sellable(sellable, quantity=quantity)
        storable = Storable(product=product, store=self.store)
        storable.increase_stock(100, get_current_branch(self.store),
                                type=StockTransactionHistory.TYPE_INITIAL,
                                object_id=None)
        return sellable

    def add_payments(self, obj, method_type=u'money', installments=1,
                     date=None):
        from stoqlib.domain.payment.payment import Payment
        from stoqlib.domain.purchase import PurchaseOrder
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.stockdecrease import StockDecrease
        assert installments > 0
        if not date:
            date = localnow()
        elif isinstance(date, datetime.date):
            date = localdate(date.year, date.month, date.day)

        if isinstance(obj, (Sale, StockDecrease)):
            if isinstance(obj, Sale):
                value = obj.get_total_sale_amount()
            else:
                value = obj.get_total_cost()
            payment_type = Payment.TYPE_IN
        elif isinstance(obj, PurchaseOrder):
            value = obj.purchase_total
            payment_type = Payment.TYPE_OUT
        else:  # pragma: nocover
            raise ValueError(obj)

        method = self.get_payment_method(method_type)
        payments = method.create_payments(
            payment_type=payment_type,
            group=obj.group,
            branch=obj.branch,
            value=value,
            due_dates=self.create_installment_dates(date, installments))
        for p in payments:
            p.open_date = date

        return payments

    def create_installment_dates(self, date, installments):
        due_dates = []
        for i in range(installments):
            due_dates.append(date + datetime.timedelta(days=i))
        return due_dates

    def create_account(self, description=None):
        from stoqlib.domain.account import Account
        return Account(description=description or u"Test Account",
                       account_type=Account.TYPE_CASH,
                       store=self.store)

    def create_account_transaction(self, account=None, value=1,
                                   source=None, incoming=False, code=None):
        from stoqlib.domain.account import AccountTransaction
        if account is None:
            account = self.create_account()

        if source:
            source_id = source.id
        else:
            source_id = sysparam.get_object_id('IMBALANCE_ACCOUNT')

        if incoming:
            operation_type = AccountTransaction.TYPE_IN
        else:
            operation_type = AccountTransaction.TYPE_OUT

        return AccountTransaction(
            description=u"Test Account Transaction",
            code=code or u"Code",
            date=localnow(),
            value=value,
            account=account,
            source_account_id=source_id,
            operation_type=operation_type,
            store=self.store)

    def create_transfer(self):
        from stoqlib.domain.transfer import TransferOrder
        return TransferOrder(source_branch=self.create_branch(),
                             destination_branch=self.create_branch(),
                             source_responsible=self.create_employee(),
                             destination_responsible=self.create_employee(),
                             store=self.store)

    def create_payment_category(self, name=u'category', category_type=None):
        from stoqlib.domain.payment.category import PaymentCategory
        return PaymentCategory(name=name,
                               color=u'#ff0000',
                               store=self.store,
                               category_type=category_type or PaymentCategory.TYPE_PAYABLE)

    def create_fiscal_day_history(self):
        from stoqlib.domain.devices import FiscalDayHistory
        return FiscalDayHistory(emission_date=localnow(),
                                reduction_date=localnow(),
                                serial=u"123456",
                                serial_id=12345,
                                coupon_start=1,
                                coupon_end=100,
                                cro=1,
                                crz=1,
                                period_total=100,
                                total=100,
                                station=self.create_station(),
                                store=self.store)

    def create_call(self, person=None, attendant=None):
        from stoqlib.domain.person import Calls
        return Calls(date=localdate(2011, 1, 1),
                     message=u"Test call message",
                     person=person or self.create_person(),
                     attendant=attendant or self.create_user(),
                     description=u"Test call",
                     store=self.store)

    def create_credit_check_history(self, user=None, client=None):
        from stoqlib.domain.person import CreditCheckHistory
        return CreditCheckHistory(check_date=localdate(2011, 1, 1),
                                  identifier=u"identifier123",
                                  status=CreditCheckHistory.STATUS_NOT_INCLUDED,
                                  notes=u"random note",
                                  user=user or self.create_user(),
                                  client=client or self.create_client(),
                                  store=self.store)

    def create_commission_source(self, category):
        from stoqlib.domain.commission import CommissionSource
        return CommissionSource(direct_value=10,
                                category=category,
                                sellable=None,
                                installments_value=1,
                                store=self.store)

    def create_invoice_printer(self):
        from stoqlib.domain.invoice import InvoicePrinter
        return InvoicePrinter(device_name=u'/dev/ttyS0',
                              description=u'Invoice Printer',
                              store=self.store)

    def create_delivery(self):
        from stoqlib.domain.sale import Delivery
        return Delivery(store=self.store)

    def create_work_permit_data(self):
        from stoqlib.domain.person import WorkPermitData
        return WorkPermitData(store=self.store)

    def create_military_data(self):
        from stoqlib.domain.person import MilitaryData
        return MilitaryData(store=self.store)

    def create_voter_data(self):
        from stoqlib.domain.person import VoterData
        return VoterData(store=self.store)

    def create_image(self):
        from stoqlib.domain.image import Image
        return Image(
            store=self.store,
            description=u"Test image",
        )

    def create_payment_renegotiation(self, group=None):
        from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
        return PaymentRenegotiation(responsible=get_current_user(self.store),
                                    branch=get_current_branch(self.store),
                                    group=group or self.create_payment_group(),
                                    client=self.create_client(),
                                    store=self.store)

    def create_cost_center(self, name=u'Cost Center', is_active=True):
        from stoqlib.domain.costcenter import CostCenter
        return CostCenter(name=name, is_active=is_active, store=self.store)

    def create_cost_center_entry(self, cost_center=None, payment=None,
                                 stock_transaction=None):
        if not payment and not stock_transaction:
            payment = self.create_payment()

        from stoqlib.domain.costcenter import CostCenterEntry
        return CostCenterEntry(cost_center=cost_center or self.create_cost_center(),
                               payment=payment,
                               stock_transaction=stock_transaction)
