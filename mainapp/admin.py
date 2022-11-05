from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.contrib import admin
from PIL import Image
# импортируем все из моделей
from .models import *
# Color for text.
from django.utils.safestring import mark_safe



class SmartphoneAdminForm(ModelForm):
    """Рендер формы на установку флажка SD."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(kwargs)
        instance = kwargs.get('instance')
        print(instance)
        if  not instance:
            self.fields['sd_volume_max'].widget.attrs.update({
                'readonly':True, 'style': 'background: lightgray'
            })

    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_volume_max']=None
        return self.cleaned_data


class NotebookAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            """<span style = "color:red; font-size:14px"> При загрузке изображения с разрешением больше {}X{} оно будет обрезано!</span>""".format(
                *Product.MAX_RESOLUTION
            ))

    # def __init__(self, *args, **kwargs):
    #     """
    #     В админке отображает help text под кнойпкой загрузки изображения?
    #     Напоминпние админу о размере изображения.
    #     """
    #     super().__init__(*args, **kwargs)
    #     self.fields['image'].help_text = mark_safe(
    #         '<span style = "color:red; font-size:14px"> Загружайте изображение с минимальным разрещением {}X{}, и с максимальным разрещением {}X{}'.format(
    #         *Product.MIN_RESOLUTION, *Product.MAX_RESOLUTION
    #         ))
    # def clean_image(self):
    #     """
    #     Проверка загружаемого изображения на минимальные параметры и максимальные.
    #     """
    #     image = self.cleaned_data['image']
    #     img = Image.open(image)
    #     min_height, min_width = Product.MIN_RESOLUTION
    #     max_height, max_width = Product.MAX_RESOLUTION
    #     if image.size > Product.MAX_IMAGE_SIZE:
    #         raise ValidationError('Размер изображения не должен привышать 3Mb!')
    #     if  img.height < min_height or img.width < min_width:
    #         raise ValidationError('Разрешение изображения меньше минимально разрешенного!')
    #     if  img.height > max_height or img.width > max_width:
    #         raise ValidationError('Разрешение изображения больше максимально разрешенного!')
    #     return image


class NotebookAdmin(admin.ModelAdmin):
    form = NotebookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Для того чтобы выбералась только категория ноутбуков а не все категории."""
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):
    change_form_template = 'admin.html'
    form = SmartphoneAdminForm
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Для того чтобы выбералась только категория смартфонов а не все категории."""
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)
admin.site.register(Notebook, NotebookAdmin)
admin.site.register(Smartphone, SmartphoneAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
