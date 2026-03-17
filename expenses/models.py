from django.db import models

class ExpenseCategory(models.Model):
    """
    支出类别模型，支持一级和二级分类。
    name: 类别名称（如 '交通' 或 '生鲜果蔬'）
    parent: 父级类别（用于创建树状结构）。如果为 None，则是一级分类。
    """
    name = models.CharField(max_length=50, verbose_name='类别名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='父类别')

    class Meta:
        db_table = 'expense_category'
        verbose_name = '支出类别'
        verbose_name_plural = '支出类别'

    def __str__(self):
        # 如果有父类，返回 "父类 > 子类" 格式，否则只返回名称
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_full_path(self):
        """获取该分类的完整路径（例如：购物 > 生鲜果蔬）"""
        path_parts = []
        current = self
        while current is not None:
            path_parts.append(current.name)
            current = current.parent
        return " > ".join(reversed(path_parts))

class Expense(models.Model):
    date = models.DateField(verbose_name='日期')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, verbose_name='类别')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')

    class Meta:
        db_table = 'expense'
        verbose_name = '开支'
        verbose_name_plural = '开支'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.category.get_full_path()}: ¥{self.amount}"