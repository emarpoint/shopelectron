from django import template
from django.utils.safestring import mark_safe
from mainapp.models import Smartphone
register = template.Library()

TABLE_HEAD = """

    <table class="table">
        <tbody>

    """
TABLE_TAIL = """
       </tbody>
      </table>

"""

TABLE_CONTENT = """
        <tr>
            <td>{name}</td>
            <td>{value}</td>
        </tr>

"""


PRODUCT_SPEC = {
    'notebook': {
        'Диагональ': 'diagonal',
        'Тип дисплея': 'display_type',
        'Частота процессора': 'processor_freq',
        'Оперативная память': 'ram',
        'Видеокарта': 'video',
        'Время работы от аккумулятора': 'time_without_charge',
    },
    'smartphone': {
        'Диагональ': 'diagonal',
        'Тип дисплея': 'display_type',
        'Разрещение экрана': 'resolution',
        'Объем батарее': 'acum_volume',
        'Оперативная память': 'ram',
        'Максимальный объем встраиваемой памяти': 'sd_volume_max',
        'Наличие слота карты': 'sd',
        'Фронтальная камера (мп)': 'frontal_cam_np',
    }    
}


def get_product_spec(product, model_name):
    table_content = ''
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


 
@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, Smartphone):
        if not product.sd:
            PRODUCT_SPEC['smartphone'].pop('Максимальный объем встраиваемой памяти')
        else:
            PRODUCT_SPEC['smartphone']['Максимальный объем встраиваемой памяти'] = 'sd_volume_max'

    return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)