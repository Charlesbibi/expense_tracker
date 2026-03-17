create table expense
(
    id          int auto_increment
        primary key,
    date        date           not null,
    description varchar(200)   not null,
    amount      decimal(10, 2) not null,
    category_id int            not null,
    constraint expense_category_id_7f4d2c7e_fk_expense_c
        foreign key (category_id) references expense_category (id)
);

create table expense_category
(
    id        int auto_increment
        primary key,
    name      varchar(50) not null,
    parent_id int         null,
    constraint expense_category_parent_id_12345678_fk_expense_c
        foreign key (parent_id) references expense_category (id)
);

create index expense_category_id_7f4d2c7e_idx
    on expense (category_id);

create index expense_date_9b6d9e_idx
    on expense (date);