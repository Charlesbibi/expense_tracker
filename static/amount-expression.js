/**
 * 金额表达式求值（与后端 expenses/amount_expr.py 规则保持一致）
 * 仅允许：数字、+ - * /、( )、小数点、空白；全角符号自动归一化。
 * 结果四舍五入到「分」。
 *
 * 用法：
 *   const r = window.evalAmountExpression('12.33+4.59+3.58*6-1');
 *   // r => { ok: true, value: 37.4 } 或 { ok: false, error: '...' }
 */
(function () {
    'use strict';

    var FULLWIDTH = {
        '＋': '+', '－': '-', '﹣': '-', '＊': '*', '×': '*',
        '／': '/', '÷': '/', '（': '(', '）': ')', '。': '.', '．': '.',
        '，': '', '、': '', '　': ' ', '¥': '', '￥': '', '＄': '', '$': ''
    };

    function normalize(raw) {
        var text = String(raw == null ? '' : raw);
        var out = '';
        for (var i = 0; i < text.length; i++) {
            var ch = text.charAt(i);
            var code = text.charCodeAt(i);
            // 全角数字 ０-９
            if (code >= 0xFF10 && code <= 0xFF19) {
                out += String.fromCharCode(code - 0xFEE0);
            } else if (Object.prototype.hasOwnProperty.call(FULLWIDTH, ch)) {
                out += FULLWIDTH[ch];
            } else {
                out += ch;
            }
        }
        return out.replace(/\s+/g, ' ').trim();
    }

    // ── 递归下降解析：expr → term (('+'|'-') term)* ───────────
    function Parser(src) {
        this.src = src;
        this.pos = 0;
    }
    Parser.prototype.peek = function () {
        return this.src.charAt(this.pos);
    };
    Parser.prototype.eat = function (ch) {
        if (this.peek() === ch) { this.pos++; return true; }
        return false;
    };
    Parser.prototype.skipSpace = function () {
        while (this.pos < this.src.length && /\s/.test(this.src.charAt(this.pos))) this.pos++;
    };
    Parser.prototype.parseExpression = function () {
        var value = this.parseTerm();
        for (;;) {
            this.skipSpace();
            var ch = this.peek();
            if (ch === '+') { this.pos++; value += this.parseTerm(); }
            else if (ch === '-') { this.pos++; value -= this.parseTerm(); }
            else return value;
        }
    };
    Parser.prototype.parseTerm = function () {
        var value = this.parseFactor();
        for (;;) {
            this.skipSpace();
            var ch = this.peek();
            if (ch === '*') { this.pos++; value *= this.parseFactor(); }
            else if (ch === '/') {
                this.pos++;
                var divisor = this.parseFactor();
                if (divisor === 0) throw new Error('表达式中存在除以零的计算');
                value /= divisor;
            } else return value;
        }
    };
    Parser.prototype.parseFactor = function () {
        this.skipSpace();
        var ch = this.peek();
        if (ch === '+') { this.pos++; return this.parseFactor(); }
        if (ch === '-') { this.pos++; return -this.parseFactor(); }
        if (ch === '(') {
            this.pos++;
            var value = this.parseExpression();
            this.skipSpace();
            if (!this.eat(')')) throw new Error('括号不匹配，请检查表达式');
            return value;
        }
        return this.parseNumber();
    };
    Parser.prototype.parseNumber = function () {
        this.skipSpace();
        var start = this.pos;
        while (this.pos < this.src.length && /[0-9]/.test(this.src.charAt(this.pos))) this.pos++;
        if (this.pos < this.src.length && this.src.charAt(this.pos) === '.') {
            this.pos++;
            while (this.pos < this.src.length && /[0-9]/.test(this.src.charAt(this.pos))) this.pos++;
        }
        if (this.pos === start) throw new Error('金额表达式格式有误，请检查数字与运算符');
        var text = this.src.slice(start, this.pos);
        var num = parseFloat(text);
        if (isNaN(num)) throw new Error('金额表达式格式有误，请检查数字与运算符');
        return num;
    };

    /**
     * 求值入口
     * @param {string} raw 用户输入的金额表达式
     * @returns {{ok: boolean, value?: number, error?: string}}
     */
    window.evalAmountExpression = function (raw) {
        try {
            var text = normalize(raw);
            if (!text) return { ok: false, error: '请输入金额' };
            if (!/^[0-9+\-*/().\s]+$/.test(text)) {
                return { ok: false, error: '金额只能包含数字和 + - * / ( ) 运算符' };
            }
            if (!/[0-9]/.test(text)) return { ok: false, error: '请输入有效数字' };

            var parser = new Parser(text);
            var value = parser.parseExpression();
            parser.skipSpace();
            if (parser.pos !== text.length) throw new Error('金额表达式格式有误，请检查括号与运算符');
            if (!isFinite(value)) return { ok: false, error: '金额计算结果无效' };

            // 四舍五入到分（与后端 ROUND_HALF_UP 对齐，规避浮点表示误差）
            var rounded = Math.round(value * 100 + (value > 0 ? 1e-9 : -1e-9)) / 100;
            return { ok: true, value: rounded };
        } catch (err) {
            return { ok: false, error: err.message || '金额表达式格式有误' };
        }
    };

    /** 金额格式化：¥1,234.56 */
    window.formatAmountValue = function (value) {
        var fixed = Math.abs(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return (value < 0 ? '-¥' : '¥') + fixed;
    };

    /**
     * 绑定输入框的实时合计提示
     * @param {HTMLInputElement} input 金额输入框
     * @param {HTMLElement} hintEl 提示容器（可为 null）
     * @returns {{value: number|null, ok: boolean}} 当前求值结果
     */
    window.bindAmountExpressionHint = function (input, hintEl) {
        if (!input) return { value: null, ok: false };
        function update() {
            var raw = input.value;
            var result = window.evalAmountExpression(raw);
            if (!hintEl) return result;
            hintEl.classList.remove('is-error', 'is-ok');
            if (!raw.trim()) {
                hintEl.textContent = '';
                return result;
            }
            if (result.ok) {
                hintEl.textContent = '= ' + window.formatAmountValue(result.value);
                hintEl.classList.add('is-ok');
            } else {
                hintEl.textContent = result.error;
                hintEl.classList.add('is-error');
            }
            return result;
        }
        input.addEventListener('input', update);
        input.addEventListener('blur', update);
        // 输入过滤：只允许数字与四则运算符（含全角自动转换交由求值器处理）
        input.addEventListener('beforeinput', function (e) {
            if (!e.data) return;
            if (/[^0-9+\-*/().\s＋－＊／（）]/.test(e.data)) {
                e.preventDefault();
            }
        });
        update();
        return update();
    };
})();
