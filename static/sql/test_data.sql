-- 插入一级分类 (parent_id 为 NULL)
INSERT INTO expense_category (name, parent_id) VALUES
('餐饮', NULL),
('交通', NULL),
('购物', NULL),
('娱乐', NULL),
('住房', NULL),
('医疗', NULL),
('教育', NULL),
('理财', NULL);

-- 插入二级分类 (parent_id 指向上一级分类的 id)
-- 假设 '餐饮' 的 id 是 1
INSERT INTO expense_category (name, parent_id) VALUES
('早餐', 1),
('午餐', 1),
('晚餐', 1),
('水果零食', 1);

-- 假设 '交通' 的 id 是 2
INSERT INTO expense_category (name, parent_id) VALUES
('公交地铁', 2),
('打车', 2),
('私家车费用', 2);

-- 假设 '购物' 的 id 是 3
INSERT INTO expense_category (name, parent_id) VALUES
('衣服鞋帽', 3),
('数码产品', 3),
('生活用品', 3);

-- 假设 '娱乐' 的 id 是 4
INSERT INTO expense_category (name, parent_id) VALUES
('电影', 4),
('游戏', 4),
('旅游', 4);

-- 假设 '住房' 的 id 是 5
INSERT INTO expense_category (name, parent_id) VALUES
('房租', 5),
('水电燃气', 5),
('物业管理', 5);

-- 假设 '医疗' 的 id 是 6
INSERT INTO expense_category (name, parent_id) VALUES
('药品', 6),
('挂号费', 6);

-- 假设 '教育' 的 id 是 7
INSERT INTO expense_category (name, parent_id) VALUES
('书籍', 7),
('培训', 7);

-- 假设 '理财' 的 id 是 8
INSERT INTO expense_category (name, parent_id) VALUES
('基金', 8),
('股票', 8);

-- 插入样例开支记录
-- 注意：这里的 category_id 需要根据上面插入的数据的实际 ID 进行调整
-- 为了方便，我们假设上面的插入顺序和 ID 是连续的，即 '早餐' 的 ID 是 9, '午餐' 是 10, 以此类推
INSERT INTO expense (date, description, amount, category_id) VALUES
('2024-03-01', '麦当劳午餐', 32.50, 10), -- 午餐
('2024-03-01', '苹果手机壳', 29.90, 21), -- 生活用品
('2024-03-02', '超市购物', 128.70, 21), -- 生活用品
('2024-03-02', '滴滴快车回家', 25.00, 15), -- 打车
('2024-03-03', '《Django实战》', 89.00, 31), -- 书籍
('2024-03-04', '健身房月卡', 299.00, 4), -- 娱乐
('2024-03-05', '早餐豆浆油条', 8.00, 9), -- 早餐
('2024-03-05', '电费缴费', 180.50, 27), -- 水电燃气
('2024-03-06', '朋友聚餐', 156.00, 11), -- 晚餐
('2024-03-07', '地铁月票', 100.00, 14), -- 公交地铁
('2024-03-08', '新书包', 120.00, 18), -- 衣服鞋帽
('2024-03-09', '周末短途游', 450.00, 35), -- 旅游
('2024-03-10', '感冒药', 45.60, 37), -- 药品
('2024-03-11', '在线课程订阅', 199.00, 32), -- 培训
('2024-03-12', '投资股票', 2000.00, 40); -- 股票