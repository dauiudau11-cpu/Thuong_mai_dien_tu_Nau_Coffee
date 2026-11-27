"""Admin-only labels without modifying models, schema, permissions or saved values."""
from copy import copy
from django.contrib import admin
from django.contrib.admin.utils import get_fields_from_path
from django.db import models
from .localization import FIELD_LABELS, MODEL_NAMES, DISPLAY_VALUES, display_value, model_name, object_label


class LocalizedOptions:
    """Request-local display facade; the actual model Options remains untouched."""
    def __init__(self, opts):
        self._opts = opts
        self.verbose_name = self.verbose_name_plural = model_name(opts.model)
        self.app_config = copy(opts.app_config)
        self.app_config.verbose_name = MODEL_NAMES.get(opts.app_label, (opts.app_config.verbose_name, {}))[0]

    def __getattr__(self, name):
        return getattr(self._opts, name)


def localized_options(opts):
    return LocalizedOptions(opts)


class VietnameseAdminMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if field is not None:
            field.label = FIELD_LABELS.get(db_field.name, field.label)
            if db_field.choices:
                field.choices = [(key, display_value(key) if str(key) in DISPLAY_VALUES else label) for key, label in field.choices]
            if hasattr(field, 'label_from_instance'):
                field.label_from_instance = object_label
        return field

    def get_action_choices(self, request, default_choices=None):
        from django.db.models.fields import BLANK_CHOICE_DASH
        choices = list(BLANK_CHOICE_DASH if default_choices is None else default_choices)
        labels = {'verbose_name': model_name(self.model), 'verbose_name_plural': model_name(self.model)}
        for _, name, description in self.get_actions(request).values():
            choices.append((name, description % labels))
        return choices

    def message_user(self, request, message, level=20, extra_tags='', fail_silently=False):
        from django.utils.safestring import SafeData, mark_safe
        text = str(message)
        safe = isinstance(text, SafeData)
        original = str(self.model._meta.verbose_name)
        translated = model_name(self.model)
        # Native success messages start with the model noun, before the quoted object.
        if text.startswith(original + ' “'):
            text = translated + text[len(original):]
        text = text.replace('thêm một ' + original + ' khác', 'thêm một ' + translated.lower() + ' khác')
        return super().message_user(request, mark_safe(text) if safe else text, level, extra_tags, fail_silently)

    def get_form(self, request, obj=None, change=False, **kwargs):
        base = super().get_form(request, obj, change=change, **kwargs)
        model = self.model
        class VietnameseForm(base):
            def _update_errors(self, errors):
                # Preserve ValidationError codes and validation results; translate params only.
                groups = errors.error_dict.values() if hasattr(errors, 'error_dict') else [errors.error_list]
                for group in groups:
                    for error in group:
                        if error.params:
                            params = dict(error.params)
                            if 'model_name' in params:
                                params['model_name'] = model_name(model)
                            for key in ('field_label', 'field_labels'):
                                if key in params:
                                    value = str(params[key])
                                    for field in model._meta.fields:
                                        value = value.replace(str(field.verbose_name), FIELD_LABELS.get(field.name, str(field.verbose_name)))
                                    params[key] = value
                            error.params = params
                return super()._update_errors(errors)
        return VietnameseForm

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        output = []
        for name in fields:
            if not isinstance(name, str) or (name != '__str__' and name not in FIELD_LABELS):
                output.append(name)
                continue
            field = None if name == '__str__' else self.model._meta.get_field(name)
            # Keep Django's native Boolean icons, ordering and field formatting.
            if field is not None and isinstance(field, models.BooleanField):
                def value(obj, key=name):
                    return getattr(obj, key)
                value.boolean = True
            else:
                def value(obj, key=name, db_field=field):
                    from django.contrib.admin.utils import display_for_field
                    if key == '__str__':
                        return object_label(obj)
                    item = getattr(obj, key)
                    if isinstance(item, models.Model):
                        return object_label(item)
                    if db_field.choices:
                        return display_value(item) if str(item) in DISPLAY_VALUES else getattr(obj, f'get_{key}_display')()
                    if key in ('original_price','sale_price','ingredient_cost','subtotal','discount','shipping','total','min_subtotal','cap','unit_price','line_total','delivery_fee','free_delivery_min') and item is not None:
                        from .templatetags.nau_ui import vnd
                        return vnd(item)
                    return display_for_field(item, db_field, self.get_empty_value_display())
            value.__name__ = name
            value.short_description = model_name(self.model) if name == '__str__' else FIELD_LABELS[name]
            if name != '__str__':
                value.admin_order_field = name
            output.append(value)
        return output

    def get_list_filter(self, request):
        filters = []
        for entry in super().get_list_filter(request):
            if not isinstance(entry, str):
                filters.append(entry)
                continue
            field = get_fields_from_path(self.model, entry)[-1]
            factory = admin.FieldListFilter.create(field, request, {}, self.model, self, entry)
            base = type(factory)
            class VietnameseFilter(base):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.title = FIELD_LABELS.get(self.field.name, self.title)

                def choices(self, changelist):
                    # Django filters own lookup_choices: related filters use pairs,
                    # AllValuesFieldListFilter uses scalar values (including ints).
                    # Localize the shared rendering contract, never their query data.
                    for choice in super().choices(changelist):
                        yield {**choice, 'display': display_value(choice['display'])}
            filters.append((entry, VietnameseFilter))
        return filters

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)
        cl.opts = localized_options(cl.opts)
        cl.title = f'Danh sách {model_name(self.model).lower()}'
        return cl

    def _localize_response(self, response, obj=None):
        context = getattr(response, 'context_data', None)
        if context and 'opts' in context:
            context['opts'] = localized_options(self.model._meta)
            context['subtitle'] = object_label(obj) if obj is not None else context.get('subtitle')
            if 'adminform' in context:
                context['title'] = ('Thêm ' if context.get('add') else 'Xem / sửa ') + model_name(self.model).lower()
            for inline in context.get('inline_admin_formsets', []):
                inline.opts.verbose_name = inline.opts.verbose_name_plural = model_name(inline.opts.model)
                for form in inline.formset.forms:
                    for name, field in form.fields.items():
                        field.label = FIELD_LABELS.get(name, field.label)
        return response

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        return self._localize_response(super().render_change_form(request, context, add, change, form_url, obj), obj)

    def render_delete_form(self, request, context):
        context['title'] = 'Xóa ' + model_name(self.model).lower()
        return self._localize_response(super().render_delete_form(request, context))

    def history_view(self, request, object_id, extra_context=None):
        response = super().history_view(request, object_id, extra_context)
        response = self._localize_response(response)
        if getattr(response, 'context_data', None):
            response.context_data['title'] = 'Lịch sử ' + model_name(self.model).lower()
        return response
