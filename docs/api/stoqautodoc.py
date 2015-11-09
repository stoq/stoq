from sphinx.ext.autodoc import AttributeDocumenter

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
                remote_key = col._remote_key
                if isinstance(remote_key, tuple):
                    remote_key = remote_key[0]

                if isinstance(remote_key, PropertyColumn):
                    name = remote_key.cls.__name__
                else:
                    name = remote_key.split('.')[0]

                value = u'**reference to:** *%s*' % (name, )
            else:
                name = col.__class__.__name__
                if name == 'AutoUnicode':
                    name = 'Unicode'
                value = u'**column:** *%s*' % (name, )
            self.add_line(value, '<autodoc>')
            self.add_line(u'', '<autodoc>')

        AttributeDocumenter.add_content(self, more_content,
                                        no_docstring=no_docstring)


def setup(app):
    app.add_autodocumenter(PropertyColumnDocumenter)
