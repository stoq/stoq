EPYDOC=epydoc

MODULES=../../../stoqlib/reporting/base/__init__.py \
	../../../stoqlib/reporting/base/default_style.py \
	../../../stoqlib/reporting/base/flowables.py \
	../../../stoqlib/reporting/base/printing.py \
	../../../stoqlib/reporting/base/tables.py \
	../../../stoqlib/reporting/base/template.py

PROGRAM_NAME=Stoqlib\ Reporting

all: html

pdf: $(MODULES)
	$(EPYDOC) --pdf -o pdf -n $(PROGRAM_NAME) $(MODULES)

html: $(MODULES)
	$(EPYDOC) -c epydoc.css --no-frames -o html -n $(PROGRAM_NAME) $(MODULES)
 
clean: 
	rm -rf pdf/ html/
