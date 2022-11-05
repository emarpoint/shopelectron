from django import forms
from django import forms

from .models import Order


class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """ Изминение отображения в форме на html странице order_date на Дата получения заказа """
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Дата получения заказа'

    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Order
        fields = (
            'first_name', 'last_name', 'phone', 'address', 'buying_type', 'order_date', 'comment'
        )