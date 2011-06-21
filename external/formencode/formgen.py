## FunFormKit, a Webware Form processor
## Copyright (C) 2001, Ian Bicking <ianb@colorstudy.com>
##
## This library is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public
## License as published by the Free Software Foundation; either
## version 2.1 of the License, or (at your option) any later version.
##
## This library is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public
## License along with this library; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
## NOTE: In the context of the Python environment, I interpret "dynamic
## linking" as importing -- thus the LGPL applies to the contents of
## the modules, but make no requirements on code importing these
## modules.
"""
Fields for use with Forms.  The Field class gives the basic interface,
and then there's bunches of classes for the specific kinds of fields.

It's not unreasonable to do a import * from this module.
"""

import string, re, urllib, cgi
PILImage = None
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import time, md5, whrandom, os
from htmlgen import html
True, False = (1==1), (0==1)
from declarative import Declarative, DeclarativeMeta

class NoDefault: pass

class Options(object):

    def __init__(self, name=None, **options):
        self.current_name = name
        if options.has_key('suboptions'):
            self.suboptions = options['suboptions']
            del options['suboptions']
        else:
            self.suboptions = None
        if options.has_key('parent'):
            self.parent = options['parent']
            del options['parent']
        else:
            self.parent = None
        self._option_values = options

    def get(self, name, obj):
        if self._option_values.has_key(name):
            return self._option_values[name]
        elif self.parent:
            return self.parent.get(name, obj)
        elif obj:
            return getattr(obj, name)
        else:
            return None

    def render(self, obj):
        if self.get('hidden', obj):
            return obj.html_hidden(self)
        else:
            return obj.html(self)

    def subfield(self, obj, name=None):
        if name is None:
            name = obj.name
        if self.suboptions:
            ops = self.suboptions.get(name, {})
        else:
            ops = {}
        ops['name'] = ops
        return self.__class__(parent=self, **ops)

    def description(self, obj):
        if obj.description:
            return obj.description
        return self.make_description(current_name)

    def make_description(self, name):
        return name

    def name(self, obj, adding=None):
        result = self.current_name or obj.name
        if adding:
            return result + '.' + adding
        else:
            return result

    def default(self, obj):
        return self.get('default', obj)

    def form__set(self, form):
        if self.parent:
            self.parent.form = form
        else:
            self._form = form

    def form__get(self):
        if self.parent:
            return self.parent.form
        else:
            return self._form

    def form__del(self):
        if self.parent:
            del self.parent.form
        else:
            del self._form

    form = property(form__get, form__set, form__del)

    def wrap_field(self, field):
        return field

class ZPTOptions(Options):

    def render(self, obj):
        name = self.name(obj)
        assert not self.default(obj), (
            "ZPTOptions cannot render values with preset defaults "
            "(%s has a default of %r)" % (name,
                                          self.default(obj)))
        if self.get('hidden', obj):
            return obj.zpt_html_hidden(self)
        else:
            error = html.tal__if(
                tal__condition="options/errors/%s | nothing" % name,
                tal__replace="structure options/errors/%s" % name)
            return html(error, obj.zpt_html(self))

    def zpt_value(self, obj, in_python=False):
        name = self.name(obj)
        if in_python:
            return 'request.get(%r, options.get(%r))' % (name, name)
        else:
            return 'request/%s | options/%s | nothing'

    def add_zpt_attr(self, xml, attr, value):
        if not attr.startswith('tal:'):
            attr = 'tal:%s' % attr
        cur = xml.attrib.get(attr, '')
        if cur:
            cur += '; '
        xml.attrib[attr] = cur + value
        return xml

    def wrap_field(self, field):
        if (field.attrib.get('type') == 'hidden'
            or field.tag in ('submit', 'button', 'reset')):
            return field
        name = self.name(field)
        self.add_zpt_attr(field, 'attributes',
                          'class python: test(options[\'errors\'].get(%r), %r)'
                          % (name, self.get('error_class', None)
                             or 'error'))
        return field

class Field(Declarative):

    description = None
    static = False
    hidden = False
    requires_label = True
    default = None

    def render(self, options):
        return options.render(self)
        return html(options.before(self),
                    options.render(self),
                    options.after(self))

    def html_hidden(self, options):
        """The HTML for a hidden input (<input type="hidden">)"""
        return html.input(
            type='hidden',
            name=options.name(self),
            value=options.default(self))

    def html(self, options):
        """The HTML input code"""
        raise NotImplementedError

    def zpt_hidden(self, options):
        return options.wrap_field(html.input(
            type="hidden",
            name=options.name(self),
            tal__attributes='value %s' % options.zpt_value(self)))

    def zpt_html(self, options):
        raise NotImplementedError

    def is_hidden(self, options):
        return options.subfield(self).get('hidden', self)

    def style_width(self, options):
        width = options.get('width', self)
        if width:
            if isinstance(width, int):
                width = '%s%%' % width
            return 'width: %s' % width
        else:
            return None

    def load_javascript(self, filename):
        f = open(os.path.join(os.path.dirname(__file__),
                              'javascript', filename))
        c = f.read()
        f.close()
        return c

class Form(Declarative):

    action = None
    method = "POST"
    fields = []
    form_name = None
    enctype = None

    def __init__(self, *args, **kw):
        Declarative.__init__(self, *args, **kw)

    def render(self, context):
        assert self.action, "You must provide an action"
        contents = html(
            [f.render(options) for f in self.fields])
        return html.form(
            action=options.get('action', self),
            method=options.get('method', self),
            name=options.get('form_name', self),
            enctype=options.get('enctype', self),
            c=contents)

class Layout(Field):

    append_to_label = ':'
    use_fieldset = False
    legend = None
    requires_label = False
    fieldset_class = 'formfieldset'

    def html(self, options):
        normal = []
        hidden = []
        for field in self.fields:
            if field.is_hidden(options):
                hidden.append(field.render(options.subfield(field)))
            else:
                normal.append(field)
        self.wrap(hidden, normal, options)

    def wrap(self, hidden, normal, options):
        hidden.append(self.wrap_fields(
            [self.wrap_field(field, options) for field in self.normal],
            options))
        return hidden

    def wrap_field(self, field, options):
        return html(self.format_label(field, options),
                    field.render(options.subfield(field)),
                    html.br)

    def format_label(self, field, options):
        label = ''
        subops = options.subfield(field)
        if subops.get('requires_label', field):
            label = subops.description(field)
            if label:
                label = label + options.get('append_to_label', self)
        return label

    def wrap_fields(self, rendered_fields, options):
        if not options.get('use_fieldset', self):
            return fields
        legend = options.get('legend', self)
        if legend:
            legend = html.legend(legend)
        else:
            legend = ''
        return html.fieldset(legend, fields,
                             class_=options.get('fieldset_class', self))

class TableLayout(Layout):

    width = None
    label_class = 'formlabel'
    field_class = 'formfield'
    label_align = None
    table_class = 'formtable'


    def wrap_field(self, field, options):
        return html.tr(
            html.td(self.format_label(field, options),
                    align=options.get('label_align', self),
                    class_=options.get('label_class', self)),
            html.td(field.render(options.subfield(field)),
                    class_=options.get('field_class', self)))

    def wrap_fields(self, rendered_fields, options):
        return html.table(rendered_fields,
                          width=options.get('width', self),
                          class_=options.get('table_class', self))

class FormTableLayout(Layout):

    layout = None
    append_to_label = ''

    def wrap(self, hidden, normal, options):
        fields = {}
        for field in normal:
            fields[field.name] = field
        layout = options.get('layout', self)
        assert layout, "You must provide a layout for %s" % self
        output = []
        for line in layout:
            if isinstance(line, (str, unicode)):
                line = [line]
            output.append(self.html_line(line, fields, options))
        hidden.append(self.wrap_fields(output, options))
        return hidden

    def html_line(self, line, fields, options):
        """
        Formats lines: '=text' means a literal of 'text', 'name' means
        the named field, ':name' means the named field, but without a
        label.
        """
        cells = []
        for item in line:
            if item.startswith('='):
                cells.append(html.td(item))
                continue
            if item.startswith(':'):
                field = fields[item[1:]]
                label = ''
            else:
                field = fields[item]
                label = self.format_label(field, options)
            if label:
                label = html(label, html.br)
            cells.append(html.td('\n', label,
                                 field.render(options.subfield(field)),
                                 valign="bottom"))
            cells.append('\n')
        return html.table(html.tr(cells))

class SubmitButton(Field):
    """
    Not really a field, but a widget of sorts.

    methodToInvoke is the name (string) of the servlet method that should
    be called when this button is hit.

    You can use suppressValidation for large-form navigation (wizards),
    when you want to save the partially-entered and perhaps invalid
    data (e.g., for the back button on a wizard).  You can load that data
    back in by passing the fields to FormRequest/From as httpRequest.

    The confirm option will use JavaScript to confirm that the user
    really wants to submit the form.  Useful for buttons that delete
    things.

    Examples::

        >>> prfield(SubmitButton(description='submit'))
        <input type="submit" value="submit" name="f" />
        >>> prfield(SubmitButton(confirm='Really?'))
        <input type="submit" value="Submit" onclick="return window.confirm(&apos;Really?&apos;)" name="f" />

    """

    confirm = None
    default_description = "Submit"
    description = ''
    requires_label = False

    def html(self, options):
        if options.get('confirm', self):
            query = ('return window.confirm(\'%s\')' %
                     javascript_quote(options.get('confirm', self)))
        else:
            query = None
        description = (options.get('description', self) or
                       options.get('default_description', self))
        return options.wrap_field(html.input(
            type='submit',
            name=options.name(self),
            value=description,
            onclick=query))

    zpt_html = html

    def html_hidden(self, options):
        if options.default(self):
            return html.input.hidden(
                name=options.name(self),
                value=options.get('description', self))
        else:
            return ''

class ImageSubmit(SubmitButton):

    """
    Like SubmitButton, but with an image.

    Examples::

        >>> prfield(ImageSubmit(), img_src='test.gif')
        <input src="test.gif" name="f" border="0" value="" type="image" alt="" />
    """

    img_height = None
    img_width = None
    border = 0

    def html(self, options):
        return html.input(
            type='image',
            name=options.name(self),
            value=options.get('description', self),
            src=options.get('img_src', self),
            height=options.get('img_height', self),
            width=options.get('img_width', self),
            border=options.get('border', self),
            alt=options.get('description', self))

class Hidden(Field):
    """
    Hidden field.  Set the value using form defaults.

    Since you'll always get string back, you are expected to only pass
    strings in (unless you use a converter like AsInt).

    Examples::

        >>> prfield(Hidden(), default='a&value')
        <input type="hidden" name="f" value="a&amp;value" />
    """

    requires_label = False
    hidden = True

    def html(self, options):
        return self.html_hidden(request)

    zpt_html = html

class Text(Field):

    """
    Basic text field.

    Examples::

        >>> t = Text()
        >>> prfield(t)
        <input type="text" name="f"/>
        >>> prfield(t, default="&whatever&")
        <input type="text" name="f" value="&amp;whatever&amp;" />
        >>> prfield(t(maxlength=20, size=10))
        <input type="text" name="f" size="10" maxlength="20" />

    ZPT::

        >>> t = Text()
        >>> prfield(t, zpt=True)
        <tal:if tal:condition="options/errors/f | nothing"
         tal:replace="structure options/errors/f" />
        <input name="f" tal:attributes="class python: test(options[&apos;errors&apos;].get(&apos;f&apos;), &apos;error&apos;); value request/%s | options/%s | nothing"
         type="text" />
    """

    size = None
    maxlength = None
    width = None

    def html(self, options):
        return options.wrap_field(html.input(
            type='text',
            name=options.name(self),
            value=options.default(self),
            maxlength=options.get('maxlength', self),
            size=options.get('size', self),
            style=self.style_width(options)))

    def zpt_html(self, options):
        return options.add_zpt_attr(
            self.html(options),
            'attributes',
            'value %s' % options.zpt_value(self))

class Textarea(Field):

    """
    Basic textarea field.  Examples::

        >>> prfield(Textarea(), default='<text>')
        <textarea name="f" rows="10" cols="60" wrap="SOFT">&lt;text&gt;</textarea>
    """

    rows = 10
    cols = 60
    wrap = "SOFT"
    width = None

    def html(self, options):
        return options.wrap_field(html.textarea(
            name=options.name(self),
            rows=options.get('rows', self),
            cols=options.get('cols', self),
            wrap=options.get('wrap', self) or None,
            style=self.style_width(options),
            c=options.default(self)))

    def zpt_html(self, options):
        return self.add_zpt_attr(
            self.html(options),
            'content', options.zpt_value(self))

class Password(Text):

    """
    Basic password field.  Examples::

        >>> prfield(Password(maxlength=10), default='pass')
        <input type="password" name="f" maxlength="10" value="pass" />
    """

    def html(self, options):
        return options.wrap_field(html.input(
            type='password',
            name=options.name(self),
            value=options.default(self),
            maxlength=options.get('maxlength', self),
            size=options.get('size', self),
            style=self.style_width(options)))

class Select(Field):
    """
    Creates a select field, based on a list of value/description
    pairs.  The values do not need to be strings.

    If nullInput is given, this will be the default value for an
    unselected box.  This would be the "Select One" selection.  If you
    want to give an error if they do not select one, then use the
    NotEmpty() validator.  They will not get this selection if the
    form is being asked for a second time after they already gave a
    selection (i.e., they can't go back to the null selection if
    they've made a selection and submitted it, but are presented the
    form again).  If you always want a null selection available,
    put that directly in the selections.

    Examples::

        >>> prfield(Select(), selections=[(1, 'One'), (2, 'Two')], default='2')
        <select name="f">
        <option value="1">One</option>
        <option value="2" selected="selected">Two</option>
        </select>
        >>> prfield(Select(selections=[(1, 'One')], null_input='Choose'))
        <select name="f">
        <option value="">Choose</option>
        <option value="1">One</option>
        </select>
    """

    selections = []
    null_input = None
    size = None

    def html(self, options, subsel=None):
        selections = options.get('selections', self)
        null_input = options.get('null_input', self)
        if not options.default(self) and null_input:
            selections = [('', null_input)] + selections
        if subsel:
            return subsel(selections, options)
        else:
            return self.selection_html(selections, options)

    def selection_html(self, selections, options):
        return options.wrap_field(html.select(
            name=options.name(self),
            size=options.get('size', self),
            c=[html.option(desc,
                           value=value,
                           selected=self.selected(value, options.default(self))
                           and "selected" or None)
               for (value, desc) in selections]))

    def zpt_html(self, options):
        return self.html(option, subsel=self.zpt_selection_html)

    def zpt_selection_html(self, selections, options):
        name = options.name(self)
        return options.wrap_field(html.select(
            name=name,
            size=options.get('size', self),
            c=[html.option(desc,
                           value=value,
                           tal_attributes="selected python: %s == %r, 'selected')"
                           % (options.zpt_value(self, in_python=True), value))]))

    def selected(self, key, default):
        if str(key) == str(default):
            return 'selected'
        else:
            return None

class Ordering(Select):

    """
    Rendered as a select field, this allows the user to reorder items.
    The result is a list of the items in the new order.

    Examples::

        >>> o = Ordering(selections=[('a', 'A'), ('b', 'B')])
        >>> prfield(o, chop=('<script ', '</script>'))
        <select name="f.func" size="2">
        <option value="a">A</option>
        <option value="b">B</option>
        </select>
        <br />
        <input type="button" value="up" onclick="up(this)" />
        <input type="button" value="down" onclick="down(this)" />
        <input type="hidden" name="f" value="a b " />
    """

    show_reset = False

    def selection_html(self, selections, options):
        size = len(selections)

        if options.default(self):
            new_selections = []
            for default_value in options.default(self):
                for value, desc in selections:
                    if str(value) == str(default_value):
                        new_selections.append((value, desc))
                        break
            assert len(new_selections) == len(selections), (
                "Defaults don't match up with the cardinality of the "
                "selections")
            selections = new_selections

        encoded_value = ''
        for key, value in selections:
            encoded_value = encoded_value + urllib.quote(str(key)) + " "

        result = []
        result.append(
            html.select(
            name=options.name(self, adding='func'),
            size=size,
            c=[html.option(desc, value=value)
               for value, desc in selections]))
        result.append(html.br())
        for name, action in self.buttons(options):
            result.append(html.input(
                type='button',
                value=name,
                onclick=action))
        result.append(html.script(
            language="JavaScript",
            type='text/javascript',
            c=html.comment(self.javascript(options))))
        result.append(html.input(
            type='hidden',
            name=options.name(self),
            value=encoded_value))
        return result

    def zpt_selection_html(self, selections, options):
        raise NotImplementedError

    def buttons(self, options):
        buttons = [('up', 'up(this)'),
                   ('down', 'down(this)')]
        if options.get('show_reset', self):
            buttons.append(('reset', 'reset_entries(this)'))
        return buttons

    def javascript(self, options):
        name = options.name(self, adding='func')
        hidden_name = options.name(self)
        return (self.load_javascript('ordering.js')
                % {'name': name, 'hidden_name': hidden_name})

class OrderingDeleting(Ordering):
    """
    Like Ordering, but also allows deleting entries

    Examples::

        >>> o = OrderingDeleting(selections=[('a', 'A'), ('b', 'B')])
        >>> prfield(o, confirm_on_delete='Yeah?', chop=('<script ', '</script>'))
        <select name="f.func" size="2">
        <option value="a">A</option>
        <option value="b">B</option>
        </select>
        <br />
        <input type="button" value="up" onclick="up(this)" />
        <input type="button" value="down" onclick="down(this)" />
        <input type="button" value="delete"
         onclick="window.confirm('Yeah?') ? delete_entry(this) : false" />
        <input type="hidden" name="f" value="a b " />
    """

    confirm_on_delete = None

    def buttons(self, options):
        buttons = Ordering.buttons(self, options)
        confirm_on_delete = options.get('confirm_on_delete', self)
        if confirm_on_delete:
            delete_button = (
                'delete',
                'window.confirm(\'%s\') ? delete_entry(this) : false'
                % javascript_quote(confirm_on_delete))
        else:
            delete_button = ('delete', 'delete_entry(this)')
        new_buttons = []
        for button in buttons:
            if button[1] == 'reset_entries(this)':
                new_buttons.append(delete_button)
                delete_button = None
            new_buttons.append(button)
        if delete_button:
            new_buttons.append(delete_button)
        return new_buttons

    def javascript(self, options):
        js = Ordering.javascript(self, options)
        return js + ('''
        function deleteEntry(formElement) {
            var select;
            select = getSelect(formElement);
            select.options[select.selectedIndex] = null;
            saveValue(select);
        }
        ''')

class Radio(Select):

    """
    Radio selection; very similar to a select, but with a radio.

    Example::

        >>> prfield(Radio(selections=[('a', 'A'), ('b', 'B')]),
        ...         default='b')
        <input type="radio" name="f" value="a" id="f_1" />
        <label for="f_1">A</label><br />
        <input type="radio" name="f" value="b" id="f_2" checked="checked" />
        <label for="f_2">B</label><br />

    """

    def selection_html(self, selections, options):
        id = 0
        result = []
        for value, desc in selections:
            id = id + 1
            if self.selected(value, options.default(self)):
                checked = 'checked'
            else:
                checked = None
            result.append(options.wrap_field(html.input(
                type='radio',
                name=options.name(self),
                value=value,
                id="%s_%i" % (options.name(self), id),
                checked=checked)))
            result.append(html.label(
                for_='%s_%i' % (options.name(self), id),
                c=desc))
            result.append(html.br())
        return result

    def zpt_selection_html(self, selections, options):
        id = 0
        result = []
        name = options.name(self)
        for value, desc in selections:
            id = id + 1
            result.append(options.wrap_field(html.input(
                type='radio',
                name=name,
                value=value,
                id="%s_%i" % (options.name(self), id),
                tal__attributes="checked python: %s == %r, 'checked')" % (options.zpt_value(self, in_python=True), value))))
            result.append(html.label(
                for_='%s_%i' % (options.name(self), id),
                c=desc))
            result.append(html.br())
        return result

class MultiSelect(Select):

    """
    Selection that allows multiple items to be selected.  A list will
    always be returned.  The size is, by default, the same as the
    number of selections (so no scrolling by the user is necessary),
    up to maxSize.

    Examples::

        >>> sel = MultiSelect(selections=[('&a', '&amp;A'), ('&b', '&amp;B'), (1, 1)])
        >>> prfield(sel)
        <select size="3" multiple="multiple" name="f">
        <option value="&amp;a">&amp;amp;A</option>
        <option value="&amp;b">&amp;amp;B</option>
        <option value="1">1</option>
        </select>
        >>> prfield(sel, default=['&b', '1'])
        <select size="3" multiple="multiple" name="f">
        <option value="&amp;a">&amp;amp;A</option>
        <option value="&amp;b" selected="selected">&amp;amp;B</option>
        <option value="1" selected="selected">1</option>
        </select>
    """

    size = NoDefault
    max_size = 10

    def selection_html(self, selections, options):
        result = []
        size = options.get('size', self)
        if size is NoDefault:
            size = min(len(selections), options.get('max_size', self))
        result.append(html.select(
            name=options.name(self),
            size=size,
            multiple="multiple",
            c=[html.option(desc,
                           value=value,
                           selected=self.selected(value, options.default(self))
                           and "selected" or None)
               for value, desc in selections]))

    def selected(self, key, default):
        if not isinstance(default, (tuple, list)):
            if default is None:
                return False
            default = [default]
        return str(key) in map(str, default)

    def html_hidden(self, options):
        default = options.default(self)
        if not isinstance(default, (tuple, list)):
            if default is None:
                default = []
            else:
                default = [default]
        return html(
            [html.input.hidden(name=options.name(self),
                               value=value)
             for value in default])

    def zpt_html_hidden(self, options):
        result = []
        name = options.name(self)
        for value, desc in options.get('selections', self):
            result.append(options.wrap_field(html.input(
                type='hidden',
                name=name,
                value=value,
                tal__condition="python: %s == %r" % (options.zpt_value(self, in_python=True), value))))
        return result

    def selection_html(self, selections, options):
        result = []
        size = options.get('size', self)
        if size is NoDefault:
            size = min(len(selections), options.get('max_size', self))
        result.append(options.wrap_field(html.select(
            name=options.name(self),
            size=size,
            multiple="multiple",
            c=[html.option(desc,
                           value=value,
                           selected=self.selected(value, options.default(self))
                           and "selected" or None)
               for value, desc in selections])))
        return result

    def zpt_selection_html(self, selections, options):
        result = []
        size = options.get('size', self)
        if size is NoDefault:
            size = min(len(selections), options.get('max_size', self))
        name = options.name(self)
        result.append(options.wrap_field(html.select(
            name=name,
            size=size,
            multiple="multiple",
            tal__define="current %s" % options.zpt_value(self),
            c=[html.option(desc,
                           value=value,
                           tal__attributes="selected python: current and %r == current or %r in current" % (value, value))
               for value, desc in selections])))
        return result

class MultiCheckbox(MultiSelect):

    """
    Like MultiSelect, but with checkboxes.

    Examples::

        >>> sel = MultiCheckbox(selections=[('&a', '&amp;A'), ('&b', '&amp;B'), (1, 1)])
        >>> prfield(sel, default='&a')
        <input type="checkbox" value="&amp;a" name="f" checked="checked"
         id="f_1" />
        <label for="f_1">&amp;amp;A</label><br />
        <input type="checkbox" value="&amp;b" name="f" id="f_2" />
        <label for="f_2">&amp;amp;B</label><br />
        <input type="checkbox" value="1" name="f" id="f_3" />
        <label for="f_3">1</label><br />
    """

    def selection_html(self, selections, options):
        result = []
        id = 0
        for value, desc in selections:
            id = id + 1
            result.append(options.wrap_field(html.input(
                type='checkbox',
                name=options.name(self),
                id="%s_%i" % (options.name(self), id),
                value=value,
                checked=self.selected(value, options.default(self))
                and "checked" or None)))
            result.append(html.label(
                " " + str(desc),
                for_="%s_%i" % (options.name(self), id)))
            result.append(html.br())
        return result

    def zpt_selection_html(self, selections, options):
        result = []
        id = 0
        for value, desc in selections:
            id = id + 1
            result.append(options.wrap_field(html.input(
                type='checkbox',
                name=options.name(self),
                id="%s_%i" % (options.name(self), id),
                value=value,
                tal__define="current %s" % options.zpt_value(self),
                tal__attributes="checked python: current and %r == current or %r current" % (value, value))))
            result.append(html.label(
                " " + str(desc),
                for_="%s_%i" % (options.name(self), id)))
            result.append(html.br())
        return result


class Checkbox(Field):

    """
    Simple checkbox.  Examples::

        >>> prfield(Checkbox(), default=0)
        <input type="checkbox" name="f" />
        >>> prfield(Checkbox(), default=1)
        <input type="checkbox" name="f" checked="checked" />

    """

    def html(self, options):
        return html.input(
            type='checkbox',
            name=options.name(self),
            checked = options.default(self) and "checked" or None)

    def zpt_html(self, options):
        return options.add_zpt_attr(
            self.html(options),
            'attributes',
            "checked python: test(%s, 'checked')"
            % (options.zpt_value(self, in_python=True)))

class File(Field):
    """
    accept is the a list of MIME types to accept.  Browsers pay
    very little attention to this, though.

    By default it will return a cgi FieldStorage object -- use .value
    to get the string, .file to get a file object, .filename to get
    the filename.  Maybe other stuff too.  If you set
    returnString=True it will return a string with the contents of the
    uploaded file.

    You can't have any validators unless you do returnString.

    Examples::

        >>> prfield(File())
        <input type="file" name="f" />
    """

    accept = None
    size = None

    def html(self, options):
        options.form.enctype = "multipart/form-data"
        accept = options.get('accept', self)
        if accept and accept is not None:
            mime_list = ",".join(accept)
        else:
            mime_list = None
        return options.wrap_field(html.input(
            type='file',
            name=options.name(self),
            size=options.get('size', self),
            accept=mime_list))

    zpt_html = html


class StaticText(Field):

    """
    A static piece of text to be put into the field, useful only
    for layout purposes.  Examples::

        >>> prfield(StaticText('some <b>HTML</b>'))
        some <b>HTML</b>
        >>> prfield(StaticText('whatever'), hidden=1)
    """

    text = ''
    requires_label = False
    __unpackargs__ = ('text',)

    def html(self, options):
        default = options.default(self)
        if default is not None:
            return str(default)
        else:
            return str(self.text)

    def html_hidden(self, options):
        return ''

    zpt_html = html

class ColorPicker(Field):

    """
    This field allows the user to pick a color from a popup window.
    This window contains a pallete of colors.  They can also enter the
    hex value of the color.  A color swatch is updated with their
    chosen color.

    Examples::

        >>> cp = ColorPicker(color_picker_url='/colorpick.html')
        >>> prfield(cp, defaults='#ff0000')
        <table border="0" cellspacing="0">
        <tr>
        <td id="f.pick"
         style=\"background-color: #ffffff; border: thin black solid;\" width="20">
          </td>
        <td>
          <input name="f"
           onchange="document.getElementById(&apos;f.pick&apos;).style.backgroundColor = this.value; return true"
           size="8" type="text" />
          <input onclick="colorpick(this, &apos;f&apos;, &apos;f.pick&apos;)"
           type="button" value="pick" />
         </td>
         </tr>
         </table>
    """

    color_picker_url = None

    def html(self, options):
        js = self.javascript(options)
        color_picker_url = options.get('color_picker_url', self)
        assert color_picker_url, (
            'You must give a base URL for the color picker')
        name = options.name(self)
        color_id = options.name(self, adding='pick')
        default_color = options.default(self) or '#ffffff'
        return html.table(
            cellspacing=0, border=0,
            c=[html.tr(
            html.td(width=20, id=color_id,
                    style="background-color: %s; border: thin black solid;" % default_color,
                    c=" "),
            html.td(
            html.input(type='text', size=8,
                       onchange="document.getElementById('%s').style.backgroundColor = this.value; return true" % color_id,
                       name=name, value=options.default(self)),
            html.input(type='button', value="pick",
                       onclick="colorpick(this, '%s', '%s')" % (name, color_id))))])

    def javascript(self, options):
        return """\
function colorpick(element, textFieldName, color_id) {
    win = window.open('%s?form='
                      + escape(element.form.attributes.name.value)
                      + '&field=' + escape(textFieldName)
                      + '&colid=' + escape(color_id),
                      '_blank',
                      'dependent=no,directories=no,width=300,height=130,location=no,menubar=no,status=no,toolbar=no');
}
""" % options.get('color_picker_url', self)


########################################
## Utility functions
########################################

def javascript_quote(value):
    """I'm depending on the fact that repr falls back on single quote
    when both single and double quote are there.  Also, JavaScript uses
    the same octal \\ing that Python uses.

    Examples::

        >>> javascript_quote('a')
        'a'
        >>> javascript_quote('\\n')
        '\\\\n'
        >>> javascript_quote('\\\\')
        '\\\\\\\\'
    """
    return repr('"' + str(value))[2:-1]


def prfield(field, chop=None, zpt=False, **kw):
    """
    Prints a field, useful for doctests.
    """
    if not kw.has_key('name'):
        kw['name'] = 'f'
    if zpt:
        ops = ZPTOptions(**kw)
    else:
        ops = Options(**kw)
    ops.form = Form()
    result = html.str(field(name=kw['name']).render(ops))
    if chop:
        pos1 = result.find(chop[0])
        pos2 = result.find(chop[1])
        if pos1 == -1 or pos2 == -1:
            print 'chop (%s) not found' % repr(chop)
        else:
            result = result[:pos1] + result[pos2+len(chop[1]):]
    print result
