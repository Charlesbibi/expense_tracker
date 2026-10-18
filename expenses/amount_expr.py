"""
金额表达式求值（不使用 eval，基于 ast 白名单安全解析）。

支持的语法：
- 数字：整数 / 小数，如 12、12.33
- 运算符：+  -  *  /（含一元正负号，如 -5、3*-2）
- 括号：()
- 全角符号（＋ － ＊ ／ （ ） ０-９）会自动归一化为半角

不支持：变量、函数调用、字符串、幂运算、位运算等其它任何语法。
结果统一四舍五入到「分」并四舍五入（ROUND_HALF_UP）。
"""
import ast
import re
from decimal import Decimal, ROUND_HALF_UP

__all__ = ['AmountExpressionError', 'evaluate_amount_expression', 'AMOUNT_PATTERN']

# 允许出现的字符：数字、四则运算符、括号、小数点与空白
AMOUNT_PATTERN = re.compile(r'^[0-9+\-*/().\s]+$')

# 全角 → 半角 归一化映射
_FULLWIDTH_MAP = {
    ord('＋'): '+', ord('－'): '-', ord('﹣'): '-', ord('－'): '-',
    ord('＊'): '*', ord('×'): '*', ord('／'): '/', ord('÷'): '/',
    ord('（'): '(', ord('）'): ')', ord('。'): '.', ord('．'): '.',
    ord('，'): '', ord('、'): '', ord('　'): ' ', ord('¥'): '', ord('￥'): '',
    ord('＄'): '', ord('$'): '',
}
for _i in range(10):
    _FULLWIDTH_MAP[ord(str(_i)) + 0xFEE0] = str(_i)  # ０-９ → 0-9


class AmountExpressionError(ValueError):
    """金额表达式无法解析 / 不合法"""


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)


def _normalize(raw: str) -> str:
    """去除首尾空白、归一化全角字符、压缩内部空白"""
    text = str(raw or '').translate(_FULLWIDTH_MAP)
    return re.sub(r'\s+', ' ', text).strip()


def _eval_node(node) -> Decimal:
    """递归求值 AST 节点（白名单校验）"""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise AmountExpressionError('金额只能包含数字，不能包含其它内容')
        return Decimal(str(node.value))

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARYOPS):
            raise AmountExpressionError('不支持该运算符')
        value = _eval_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise AmountExpressionError('仅支持 + - * / 四则运算')
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        # 除法
        if right == 0:
            raise AmountExpressionError('表达式中存在除以零的计算')
        return left / right

    raise AmountExpressionError('金额表达式包含不支持的内容')


def evaluate_amount_expression(raw) -> Decimal:
    """
    将金额表达式求值为 Decimal（保留两位小数）。

    :param raw: 形如 "12.33+4.59+3.58*6-1" 的字符串；纯数字同样支持
    :raises AmountExpressionError: 表达式为空 / 含非法字符 / 语法错误 / 除零
    """
    text = _normalize(raw)
    if not text:
        raise AmountExpressionError('请输入金额')
    if not AMOUNT_PATTERN.match(text):
        raise AmountExpressionError('金额只能包含数字和 + - * / ( ) 运算符')
    if not re.search(r'\d', text):
        raise AmountExpressionError('请输入有效数字')

    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError:
        raise AmountExpressionError('金额表达式格式有误，请检查括号与运算符')

    value = _eval_node(tree)
    try:
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        raise AmountExpressionError('金额计算结果无效')
