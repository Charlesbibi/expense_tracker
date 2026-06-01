from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    # 类别只显示叶子节点（无子分类）：有二级的不显示一级，仅一级的显示自身
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.none(),  # 临时，__init__ 再设
        label='类别',
        empty_label='请选择类别'
    )

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
        # 只取叶子节点：没有子分类的类别（排除被当作 parent 的所有 id）
        parent_ids = ExpenseCategory.objects.exclude(
            parent__isnull=True
        ).values_list('parent_id', flat=True).distinct()
        leaf_qs = ExpenseCategory.objects.exclude(
            id__in=parent_ids
        ).order_by('parent__name', 'name')
        self.fields['category'].queryset = leaf_qs
        # 下拉框显示完整路径（如 购物 > 生鲜果蔬）
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_path()
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