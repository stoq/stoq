from sphinx.ext.autodoc import AttributeDocumenter

from stoqlib.domain.base import Domain
from storm.properties import PropertyColumn
from storm.references import Reference


class PropertyColumnDocumenter(AttributeDocumenter):
    objtype = 'stoqattribute'
    directivetype = 'attribute'
    priority = 110 + AttributeDocumenter.priority

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return (isinstance(member, PropertyColumn) or
                isinstance(member, Reference))

    def add_content(self, more_content, no_docstring=False):
        col = self.parent.__dict__.get(self.object_name)
        if col is not None:
            if isinstance(col, Reference):
                name = col._remote_key.split('.')[0]
                if name == 'AutoUnicode':
                    name = 'Unicode'
                value = u'**reference to:** *%s*' % (name, )
            else:
                value = u'**column:** *%s*' % (col.__class__.__name__, )
            self.add_line(value, '<autodoc>')
            self.add_line(u'', '<autodoc>')

        AttributeDocumenter.add_content(self, more_content,
                                        no_docstring=no_docstring)

def setup(app):
    app.add_autodocumenter(PropertyColumnDocumenter)
