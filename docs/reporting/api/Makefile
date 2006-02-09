EPYDOC=epydoc

MODULES=../../stoqlib/reporting/__init__.py \
		../../stoqlib/reporting/default_style.py \
		../../stoqlib/reporting/flowables.py \
		../../stoqlib/reporting/printing.py \
		../../stoqlib/reporting/tables.py \
		../../stoqlib/reporting/template.py

PROGRAM_NAME=Stoqlib\ Reporting

all: html

pdf: $(MODULES)
	$(EPYDOC) --pdf -o pdf -n $(PROGRAM_NAME) $(MODULES)

html: $(MODULES)
	$(EPYDOC) -c epydoc.css --no-frames -o html -n $(PROGRAM_NAME) $(MODULES)
 
clean: 
	rm -rf pdf/ html/
