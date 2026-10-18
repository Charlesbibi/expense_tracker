from django import forms
from decimal import Decimal
from .models import Expense, ExpenseCategory
from .amount_expr import evaluate_amount_expression, AmountExpressionError

class ExpenseForm(forms.ModelForm):
    # 类别只显示叶子节点（无子分类）：有二级的不显示一级，仅一级的显示自身
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.none(),  # 临时，__init__ 再设
        label='类别',
        empty_label='请选择类别'
    )
    # 金额支持表达式输入（如 12.33+4.59+3.58*6-1），后端求值后再落库
    amount = forms.CharField(
        label='金额（元）',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': '0.00 或 12.33+4.59+3.58*6-1',
            'inputmode': 'text',
            'autocomplete': 'off',
            'class': 'amount-expr-input',
        })
    )

    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount', 'is_big_expense']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': '请输入开支描述（可选）...'}),
        }
        labels = {
            'is_big_expense': '年度必要大额开销',
        }

    def clean_amount(self):
        """支持表达式：先安全求值，再校验结果"""
        raw = (self.cleaned_data.get('amount') or '').strip()
        try:
            amount = evaluate_amount_expression(raw)
        except AmountExpressionError as exc:
            raise forms.ValidationError(str(exc))
        if amount <= 0:
            raise forms.ValidationError('金额计算结果必须大于零（当前为 %s）。' % amount)
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
        # 年度必要大额开销为可选（复选框，不勾选即 False）
        self.fields['is_big_expense'].required = False


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