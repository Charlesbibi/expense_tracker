from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, F
from datetime import datetime
from calendar import monthrange
from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, CategoryForm


def home(request):
    """主页，重定向到开支列表"""
    return redirect('expenses:list')


def expense_list(request):
    """开支列表页面"""
    expenses = Expense.objects.all()
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # 按月筛选
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    if year and month:
        expenses = expenses.filter(date__year=year, date__month=month)
        total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # 获取所有年份用于下拉选择
    all_years = Expense.objects.dates('date', 'year', order='DESC').distinct()

    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'current_year': int(year) if year else None,
        'current_month': int(month) if month else None,
        'all_years': all_years,
    }
    return render(request, 'expenses/list.html', context)


def add_expense(request):
    """添加开支"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expenses:list')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/add.html', {'form': form})


def add_category(request):
    """新增开支类别（一级或二级）"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expenses:add_category')
    else:
        form = CategoryForm()

    # 查询所有现有类别，用于页面展示
    top_categories = ExpenseCategory.objects.filter(parent__isnull=True).prefetch_related('expensecategory_set')
    return render(request, 'expenses/add_category.html', {
        'form': form,
        'top_categories': top_categories,
    })


def delete_expense(request, pk):
    """删除开支"""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('expenses:list')  # 删除后重定向回列表页
    # 如果不是 POST 请求，也可以渲染一个确认页面，这里简化为直接重定向
    return redirect('expenses:list')


def visualizations(request):
    """可视化页面"""
    current_real_year = datetime.now().year

    # 获取年份参数，默认为当前真实年份
    year = request.GET.get('year', current_real_year)
    try:
        year = int(year)
    except ValueError:
        year = current_real_year

    # 获取可视化类型参数 (primary: 一级分类, secondary: 二级分类)，默认为一级
    viz_type = request.GET.get('viz_type', 'primary')  # primary 或 secondary

    # 获取所有有数据的年份，并确保当前年份始终出现（即便今年还没有数据）
    from datetime import date as _date
    db_years = list(Expense.objects.dates('date', 'year', order='DESC').distinct())
    db_year_ints = [d.year for d in db_years]
    if current_real_year not in db_year_ints:
        db_years = [_date(current_real_year, 1, 1)] + db_years
    all_years = db_years

    # 1. 按月统计总开支 (与之前相同)
    monthly_data = {}
    for month in range(1, 13):
        start_date = datetime(year, month, 1)
        end_day = monthrange(year, month)[1]
        end_date = datetime(year, month, end_day).date()

        total = Expense.objects.filter(
            date__range=(start_date.date(), end_date)
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        monthly_data[month] = float(total)

    # 2. 按分类统计开支占比 (根据 viz_type 决定是按一级还是二级)
    if viz_type == 'secondary':
        # 查询所有二级分类及其总金额
        category_data = Expense.objects.filter(
            date__year=year
        ).values('category__name', 'category__parent__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        # 将结果整理成两个列表：类别名和金额
        categories = []
        amounts = []
        for item in category_data:
            if item['category__parent__name']:
                full_name = f"{item['category__parent__name']} > {item['category__name']}"
            else:
                full_name = item['category__name']
            categories.append(full_name)
            amounts.append(float(item['total']))
    else:  # viz_type == 'primary'
        category_data = Expense.objects.filter(
            date__year=year
        ).values('category__parent__name', 'category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        # 将结果整理成两个列表：类别名和金额
        categories = []
        amounts = []
        for item in category_data:
            category_name = item['category__parent__name'] or item['category__name']
            categories.append(category_name)
            amounts.append(float(item['total']))

    context = {
        'monthly_data': monthly_data,
        'categories': categories,
        'amounts': amounts,
        'current_year': year,
        'all_years': all_years,
        'viz_type': viz_type,
    }
    return render(request, 'expenses/visualizations.html', context)