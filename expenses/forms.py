from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': '请输入开支描述（可选）...'}),
            'amount': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("金额必须大于零。")
        return amount

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 在初始化时，将所有分类（包括一级和二级）都添加到选择列表中
        self.fields['category'].queryset = ExpenseCategory.objects.all()
        # 描述字段为可选
        self.fields['description'].required = False


class CategoryForm(forms.ModelForm):
    """新增开支类别的表单，支持一级和二级分类"""
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '请输入类别名称，如：餐饮、早餐'}),
        }
        labels = {
            'name': '类别名称',
            'parent': '父级类别（留空则为一级分类）',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 父级只允许选择一级分类（parent 为空的），避免三级嵌套
        self.fields['parent'].queryset = ExpenseCategory.objects.filter(parent__isnull=True)
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = '-- 不选（创建为一级分类）--'