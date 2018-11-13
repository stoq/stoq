from storm.expr import And

from stoqlib.domain.uiform import UIForm, UIField


def apply_patch(store):
    forms = store.find(UIForm, UIForm.form_name != 'product')
    for form in forms:
        if store.find(UIField, And(UIField.field_name == 'cpf',
                                   UIField.ui_form == form)).any():
            continue
        UIField(store=store,
                description='Document',
                field_name='cpf',
                mandatory=False,
                visible=True,
                ui_form=form)
