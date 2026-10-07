/**
 * 类别树形下拉组件（全局共享）
 * 依赖：custom.css 中 .cat-tree 系列样式
 * 用法（模板中）：
 *   <script>window.CATEGORIES_API_URL = '{% url "expenses:api_categories" %}';</script>
 *   <script src="{% static 'category-tree.js' %}"></script>
 *   const api = initCategoryTree('catTreeRootId');
 *   api.setValue(id, '父类 > 子类'); api.getValue(); api.getFullPath();
 */
'use strict';

// ─── 类别树形下拉组件 ──────────────────────────────────────
let CATEGORY_TREE_DATA = null;  // 全局缓存，避免重复请求

function fetchCategoryTree() {
    if (CATEGORY_TREE_DATA) return Promise.resolve(CATEGORY_TREE_DATA);
    return fetch(window.CATEGORIES_API_URL, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(data => {
        if (!data.success || !data.tree) throw new Error('bad data');
        CATEGORY_TREE_DATA = data.tree;
        return CATEGORY_TREE_DATA;
    });
}

function initCategoryTree(rootId, onSelect) {
    const root = document.getElementById(rootId);
    if (!root) return null;
    const trigger = root.querySelector('.cat-tree__trigger');
    const panel = root.querySelector('.cat-tree__panel');
    const hidden = root.querySelector('input[type=hidden]');
    const valueEl = root.querySelector('.cat-tree__value');
    const api = {
        setValue(id, fullPath) {
            hidden.value = id || '';
            if (id) {
                valueEl.textContent = fullPath || '已选择';
                valueEl.classList.remove('cat-tree__value--placeholder');
            } else {
                valueEl.textContent = '请选择类别';
                valueEl.classList.add('cat-tree__value--placeholder');
            }
        },
        getValue() { return hidden.value; },
        getFullPath() { return valueEl.classList.contains('cat-tree__value--placeholder') ? '' : valueEl.textContent; },
        open() { root.classList.add('cat-tree--open'); trigger.setAttribute('aria-expanded', 'true'); },
        close() { root.classList.remove('cat-tree--open'); trigger.setAttribute('aria-expanded', 'false'); },
    };

    function selectItem(btn, fullPath) {
        // 清除所有选中态
        panel.querySelectorAll('.cat-tree__child.is-selected, .cat-tree__leaf.is-selected').forEach(el => el.classList.remove('is-selected'));
        btn.classList.add('is-selected');
        api.setValue(btn.dataset.id, fullPath);
        api.close();
        // 触发自定义事件（供大额开销自动勾选等逻辑使用）
        root.dispatchEvent(new CustomEvent('cat-tree:change', {
            bubbles: false,
            detail: { id: btn.dataset.id, fullPath: fullPath }
        }));
        if (typeof onSelect === 'function') onSelect(btn.dataset.id, fullPath);
    }

    // 构建 DOM
    fetchCategoryTree().then(tree => {
        const scroll = document.createElement('div');
        scroll.className = 'cat-tree__scroll';
        tree.forEach(node => {
            if (node.has_children) {
                // 一级类别：可展开/收起，展示子类别
                const group = document.createElement('div');
                group.className = 'cat-tree__group';
                const parentBtn = document.createElement('button');
                parentBtn.type = 'button';
                parentBtn.className = 'cat-tree__parent';
                parentBtn.innerHTML = `<i class="bi bi-folder cat-tree__parent-icon"></i><span class="cat-tree__parent-name">${node.name}</span><i class="bi bi-chevron-right cat-tree__chevron"></i><span class="cat-tree__count">${node.children.length}</span>`;
                const children = document.createElement('div');
                children.className = 'cat-tree__children';
                node.children.forEach(child => {
                    const childBtn = document.createElement('button');
                    childBtn.type = 'button';
                    childBtn.className = 'cat-tree__child';
                    childBtn.dataset.id = child.id;
                    childBtn.dataset.fullPath = `${node.name} > ${child.name}`;
                    childBtn.innerHTML = `<i class="bi bi-dot"></i><span>${child.name}</span><i class="bi bi-check2 cat-tree__check"></i>`;
                    childBtn.addEventListener('click', e => {
                        e.stopPropagation();
                        selectItem(childBtn, `${node.name} > ${child.name}`);
                    });
                    children.appendChild(childBtn);
                });
                parentBtn.addEventListener('click', () => {
                    group.classList.toggle('cat-tree__group--expanded');
                });
                group.appendChild(parentBtn);
                group.appendChild(children);
                scroll.appendChild(group);
            } else {
                // 一级且无子类：自身即叶子，样式与父级行统一（文件夹图标），点击直接选中
                const leafBtn = document.createElement('button');
                leafBtn.type = 'button';
                leafBtn.className = 'cat-tree__leaf';
                leafBtn.dataset.id = node.id;
                leafBtn.dataset.fullPath = node.name;
                leafBtn.innerHTML = `<i class="bi bi-folder cat-tree__parent-icon"></i><span class="cat-tree__parent-name">${node.name}</span><i class="bi bi-check2 cat-tree__check"></i>`;
                leafBtn.addEventListener('click', e => {
                    e.stopPropagation();
                    selectItem(leafBtn, node.name);
                });
                scroll.appendChild(leafBtn);
            }
        });
        panel.innerHTML = '';
        panel.appendChild(scroll);
    }).catch(() => { /* silently fail */ });

    // 交互：点触发器切换、点外部收起、键盘支持
    trigger.addEventListener('click', () => {
        root.classList.contains('cat-tree--open') ? api.close() : api.open();
    });
    trigger.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger.click(); }
        if (e.key === 'Escape') api.close();
    });
    document.addEventListener('click', e => {
        if (!root.contains(e.target)) api.close();
    });

    return api;
}

// 根据完整路径设置选中项（编辑弹窗回显用），如「租房开销 > 房租」
function setCategoryTreeByPath(api, rootId, fullPath) {
    const root = document.getElementById(rootId);
    if (!root || !fullPath) return;
    const btn = root.querySelector(`.cat-tree__child[data-full-path="${CSS.escape(fullPath)}"], .cat-tree__leaf[data-full-path="${CSS.escape(fullPath)}"]`);
    if (btn) {
        root.querySelectorAll('.cat-tree__child.is-selected, .cat-tree__leaf.is-selected').forEach(el => el.classList.remove('is-selected'));
        btn.classList.add('is-selected');
        // 展开所在分组
        if (btn.closest('.cat-tree__group')) btn.closest('.cat-tree__group').classList.add('cat-tree__group--expanded');
        api.setValue(btn.dataset.id, fullPath);
    }
}

// 根据类别 id 设置选中项（表单校验失败回显用）
function setCategoryTreeById(api, rootId, categoryId) {
    if (!categoryId) return;
    fetchCategoryTree().then(tree => {
        for (const node of tree) {
            if (!node.has_children && String(node.id) === String(categoryId)) {
                setCategoryTreeByPath(api, rootId, node.name);
                return;
            }
            for (const child of (node.children || [])) {
                if (String(child.id) === String(categoryId)) {
                    setCategoryTreeByPath(api, rootId, `${node.name} > ${child.name}`);
                    return;
                }
            }
        }
    }).catch(() => {});
}

// 选择「租房开销 > 房租/水电」时，自动勾选年度必要大额开销
function bindBigExpenseAutoCheck(treeRootId, checkboxId) {
    const treeRoot = document.getElementById(treeRootId);
    const checkbox = document.getElementById(checkboxId);
    if (!treeRoot || !checkbox) return;
    treeRoot.addEventListener('cat-tree:change', function(e) {
        const path = e.detail.fullPath || '';
        if (path.includes('租房开销 > 房租') || path.includes('租房开销 > 水电')) {
            checkbox.checked = true;
        }
    });
}
