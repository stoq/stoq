import datetime
import html.parser
from decimal import Decimal

from kiwi.component import provide_utility
from lxml import etree
from storm.exceptions import NotOneError

from stoqlib.database.interfaces import ICurrentBranch, ICurrentUser
from stoqlib.domain.nfe import NFeItem, NFePayment, NFePurchase, NFeSupplier
from stoqlib.domain.overrides import SellableBranchOverride
from stoqlib.domain.person import Branch, LoginUser, Person
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sellable import Sellable
from stoqlib.exceptions import NFeDifferentCNPJ, NFeImportedError


class NFe:
    namespace = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    def __init__(self, file_handler, store):
        self.store = store
        assert self.store
        element = etree.fromstring(file_handler.encode('utf-8')).getroottree()
        self.root = element.getroot()

        # In some cases the XML can start with NFe instead of nfeProc
        first_tag = "{" + self.namespace.get("nfe") + "}nfeProc"
        if first_tag == self.root.tag:
            self.root = self.root[0]

    def _find_tag(self, path, root):
        new_path = path.replace("/", "/" + list(self.namespace.keys())[0] + ":")
        if root is None:
            return self.root.xpath(new_path, namespaces=self.namespace)
        return root.xpath("." + new_path, namespaces=self.namespace)

    def _find_one_tag(self, path, root):
        tag = self._find_tag(path, root)
        if len(tag) > 0:
            return tag[0]
        return None

    def _get_text(self, path, root):
        tag = self._find_one_tag(path, root)
        if tag is not None and tag.text is not None:
            text = html.parser.HTMLParser().unescape(tag.text)
            return str(text)
        return None

    def _get_decimal(self, path, root):
        tag = self._find_one_tag(path, root)
        if tag is not None and tag.text is not None:
            return Decimal(tag.text)
        return None

    def _get_integer(self, path, root):
        tag = self._find_one_tag(path, root)
        if tag is not None and tag.text is not None:
            return int(tag.text)
        return 0

    def _get_date(self, path, root):
        tag = self._find_one_tag(path, root)
        if tag is not None and tag.text is not None:
            time = datetime.datetime.strptime(tag.text, "%Y-%m-%d")
            return time
        return None

    def _format_cnpj(self, cnpj):
        return ("{}.{}.{}/{}-{}").format(
            cnpj[0:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14])

    def _get_or_create_supplier(self):
        emit = self._find_one_tag('/infNFe/emit', self.root)
        supplier_cnpj = self._format_cnpj(self._get_text('/CNPJ', emit))
        nfe_supplier = self.store.find(NFeSupplier, cnpj=supplier_cnpj).one()

        if nfe_supplier:
            return nfe_supplier

        complement = self._get_text('/enderEmit/xCpl', emit) or u''
        try:
            street_number = self._get_integer('/enderEmit/nro', emit)
        except ValueError:
            street_number = 0
            complement = complement + ' ' + self._get_text('/enderEmit/nro', emit)

        nfe_supplier = NFeSupplier(cnpj=supplier_cnpj,
                                   name=self._get_text('/xNome', emit),
                                   fancy_name=self._get_text('/xFant', emit),
                                   postal_code=self._get_text('/enderEmit/CEP', emit),
                                   district=self._get_text('/enderEmit/xBairro', emit),
                                   street=self._get_text('/enderEmit/xLgr', emit),
                                   phone_number=self._get_text('/*/fone', emit),
                                   street_number=street_number,
                                   complement=complement,
                                   municipal_registry=self._get_text('/enderEmit/IM', emit),
                                   state_registry=self._get_text('/enderEmit/IE', emit),
                                   city_code=self._get_integer('/enderEmit/cMun', emit))

        return nfe_supplier

    # Find

    def _find_user(self):
        # FIXME Create/Use a stoq-portal user
        responsible = self.store.find(LoginUser, username=u'admin').one()
        return provide_utility(ICurrentUser, responsible, replace=True)

    def _find_branch(self, branch_id=None):
        cnpj = self._format_cnpj(self._get_text('/infNFe/dest/CNPJ', self.root))
        if branch_id:
            branch = self.store.get(Branch, branch_id)
            if cnpj != branch.person.company.cnpj:
                raise NFeDifferentCNPJ(cnpj)
        try:
            person = Person.get_by_document(self.store, cnpj)
        except NotOneError:
            # Found multiple branchs with the same CNPJ, so we get it by id
            person = self.store.get(Branch, branch_id).person if branch_id else None

        if person is None:
            return None, cnpj

        provide_utility(ICurrentBranch, person.branch, replace=True)
        return person.branch, cnpj

    # Process

    def process(self, branch_id=None):
        freight_type = self._get_integer('/infNFe/transp/modFrete', self.root)
        if freight_type == 0:
            freight_type = PurchaseOrder.FREIGHT_CIF
        else:
            freight_type = PurchaseOrder.FREIGHT_FOB

        user = self._find_user()
        branch, cnpj = self._find_branch(branch_id)
        nfe_supplier = self._get_or_create_supplier()

        invoice_number = self._get_integer('/infNFe/ide/nNF', self.root)
        invoice_series = self._get_integer('/infNFe/ide/serie', self.root)
        nfe_purchase = NFePurchase.find_purchase_order(
            self.store, nfe_supplier, invoice_number, invoice_series)

        if nfe_purchase:
            raise NFeImportedError(nfe_purchase.id)

        if not branch:
            raise NFeDifferentCNPJ(cnpj)

        nfe_purchase = NFePurchase(store=self.store, user=user, branch=branch,
                                   cnpj=cnpj, nfe_supplier=nfe_supplier,
                                   freight_type=freight_type,
                                   invoice_number=invoice_number,
                                   invoice_series=invoice_series,
                                   freight_cost=self._get_decimal('/infNFe/total/ICMSTot/vFrete',
                                                                  self.root),
                                   total_cost=self._get_decimal('/infNFe/total/ICMSTot/vNF',
                                                                self.root),
                                   xml=self.root)

        nfe_products = self._find_tag('/infNFe/det', self.root)

        # Ensure the supplier is created on Stoq's database, we'll need it to
        # create the purchase order
        nfe_purchase.find_or_create_supplier(nfe_supplier)

        # Store all products
        for item in nfe_products:
            description = self._get_text('/prod/xProd', item)
            barcode = self._get_text('/prod/cEAN', item)
            supplier_code = self._get_text('/prod/cProd', item)

            try:
                sellable = self.store.find(Sellable, barcode=barcode).one()
            except NotOneError:
                raise NotOneError('Barcode duplicated: %s' % barcode)

            NFeItem(store=self.store, nfe_purchase=nfe_purchase,
                    description=description, sellable=sellable,
                    barcode=barcode, supplier_code=supplier_code,
                    ex_tipi=self._get_text('/prod/EXTIPI', item),
                    ncm=self._get_text('/prod/NCM', item),
                    genero=self._get_text('/prod/genero', item),
                    cost=self._get_decimal('/prod/vUnCom', item),
                    freight_cost=self._get_decimal('/prod/vFrete', item) or 0,
                    insurance_cost=self._get_decimal('/prod/vSeg', item) or 0,
                    # This is something like /imposto/ICMS/ICMS*/vICMSST
                    icmsst_cost=self._get_decimal("/imposto/ICMS/" +
                                                  "*[starts-with(local-name(), 'ICMS')]/vICMSST",
                                                  item) or 0,
                    ipi_cost=self._get_decimal("/imposto/IPI/IPITrib/vIPI", item) or 0,
                    discount_value=self._get_decimal('/prod/vDesc', item) or 0,
                    quantity=self._get_decimal('/prod/qCom', item))

            if sellable and not SellableBranchOverride.find_by_sellable(
                    branch=branch, sellable=sellable):
                SellableBranchOverride(store=self.store, branch=branch, sellable=sellable)

        dups = self._find_tag('/infNFe/cobr/dup', self.root)
        for dup in dups:
            # FIXME Store the payment method
            NFePayment(store=self.store,
                       nfe_purchase=nfe_purchase,
                       value=self._get_decimal('/vDup', dup),
                       duplicate_number=self._get_text('/nDup', dup),
                       due_date=self._get_date('/dVenc', dup))

        self.store.commit()
        return nfe_purchase
