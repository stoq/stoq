# bootstrap script used to make an egg executable
# bdist_egg picks it up automatically

import sys

# This is used so bb-freeze can detect which
# imports are needed to run reportlab.
import pkg_resources
import reportlab.pdfbase._fontdata
import reportlab.pdfbase._fontdata_enc_macexpert
import reportlab.pdfbase._fontdata_enc_macroman
import reportlab.pdfbase._fontdata_enc_pdfdoc
import reportlab.pdfbase._fontdata_enc_standard
import reportlab.pdfbase._fontdata_enc_symbol
import reportlab.pdfbase._fontdata_enc_winansi
import reportlab.pdfbase._fontdata_enc_zapfdingbats
import reportlab.pdfbase._fontdata_widths_courierboldoblique
import reportlab.pdfbase._fontdata_widths_courierbold
import reportlab.pdfbase._fontdata_widths_courieroblique
import reportlab.pdfbase._fontdata_widths_courier
import reportlab.pdfbase._fontdata_widths_helveticaboldoblique
import reportlab.pdfbase._fontdata_widths_helveticabold
import reportlab.pdfbase._fontdata_widths_helveticaoblique
import reportlab.pdfbase._fontdata_widths_helvetica
import reportlab.pdfbase._fontdata_widths_symbol
import reportlab.pdfbase._fontdata_widths_timesbolditalic
import reportlab.pdfbase._fontdata_widths_timesbold
import reportlab.pdfbase._fontdata_widths_timesitalic
import reportlab.pdfbase._fontdata_widths_timesroman
import reportlab.pdfbase._fontdata_widths_zapfdingbats

from stoq.main import main

pkg_resources.require('stoqdrivers')
sys.exit(main(sys.argv))
