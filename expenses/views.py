from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
from calendar import monthrange
import json
from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, CategoryForm


def get_categories_api(request):
    """API：获取所有类别列表（用于 AJAX 加载）"""
    categories = ExpenseCategory.objects.all()
    data = [
        {
            'id': cat.id,
            'name': cat.name,
            'full_path': cat.get_full_path()
        }
        for cat in categories
    ]
    print(f"[DEBUG] 返回类别数据: {len(data)} 个类别")
    return JsonResponse({'success': True, 'categories': data})


def home(request):
    """主页，重定向到开支列表"""
    return redirect('expenses:list')


def expense_list(request):
    """开支列表页面（带分页）"""
    expenses_qs = Expense.objects.select_related('category', 'category__parent').all()

    # 按年/月筛选
    year = request.GET.get('year', '')
    month = request.GET.get('month', '')
    if year:
        expenses_qs = expenses_qs.filter(date__year=year)
    if month:
        expenses_qs = expenses_qs.filter(date__month=month)

    # 当前筛选范围内的总金额 & 总笔数（用于统计卡片，不受分页影响）
    total_expense = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    total_count   = expenses_qs.count()
    latest_date   = expenses_qs.values_list('date', flat=True).first()   # 已按 -date 排序

    # 分页：每页 15 条
    paginator   = Paginator(expenses_qs, 15)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # 获取所有年份用于下拉选择
    all_years = Expense.objects.dates('date', 'year', order='DESC').distinct()

    # 为模态框表单准备数据
    form = ExpenseForm(initial={'date': datetime.now().strftime('%Y-%m-%d')})

    # 构建分页时保留筛选参数的查询字符串（去掉 page 参数）
    query_params = request.GET.copy()
    query_params.pop('page', None)
    filter_query_string = query_params.urlencode()

    context = {
        'page_obj':            page_obj,
        'expenses':            page_obj.object_list,   # 兼容模板原有变量名
        'total_expense':       total_expense,
        'total_count':         total_count,
        'latest_date':         latest_date,
        'current_year':        int(year) if year else None,
        'current_month':       int(month) if month else None,
        'all_years':           all_years,
        'filter_query_string': filter_query_string,
        'form':                form,  # 添加表单，用于获取分类列表
    }
    return render(request, 'expenses/list.html', context)


def expense_list_clean(request):
    """开支列表纯净版（用于调试）"""
    return render(request, 'expenses/list_clean.html')


def add_expense(request):
    """添加开支（支持 AJAX 和普通提交）"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)

        # AJAX 请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print(f"[DEBUG] 收到 AJAX 请求: {request.POST}")
            if form.is_valid():
                form.save()
                print(f"[DEBUG] 表单验证成功，保存记录")
                return JsonResponse({'success': True, 'message': '开支记录已成功添加'})
            else:
                print(f"[DEBUG] 表单验证失败: {form.errors}")
                errors = {}
                for field in form.errors:
                    errors[field] = form.errors[field].as_text()
                return JsonResponse({
                    'success': False,
                    'error': '表单验证失败',
                    'errors': errors
                })
        else:
            # 普通提交
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


def modal_debug(request):
    """模态框调试页面"""
    return render(request, 'expenses/modal_debug.html')


def minimal_test(request):
    """最小化模态框测试页面"""
    return render(request, 'expenses/minimal_test.html')


def nocss_test(request):
    """无CSS测试页面"""
    return render(request, 'expenses/nocss_test.html')