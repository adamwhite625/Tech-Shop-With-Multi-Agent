DROP DATABASE tech_store_db;
CREATE DATABASE tech_store_db;
USE tech_store_db;

-- =========================
-- 1. USER & PROFILE
-- =========================

CREATE TABLE users
(
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    email    VARCHAR(100) NOT NULL UNIQUE,
    phone    VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    salt     VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    status   TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 4),
# active,inactive,suspend,banned

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE user_profiles
(
    user_id       INT PRIMARY KEY,
    first_name    VARCHAR(150),
    middle_name   VARCHAR(150),
    last_name     VARCHAR(150),
    avatar        VARCHAR(255),
    profile       TEXT,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login    DATETIME
);

CREATE TABLE roles
(
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    name   VARCHAR(150) NOT NULL,
    `desc` TEXT,

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE user_roles
(
    user_id INT,
    role_id INT,
    PRIMARY KEY (user_id, role_id)
);

-- =========================
-- 2. BLOG & CATEGORY
-- =========================

CREATE TABLE blog_posts
(
    blogpost_id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(150) NOT NULL,
    meta_title VARCHAR(150),
    slug       VARCHAR(150),
    thumb      VARCHAR(255),
    summary    TEXT,
    content    TEXT,
    conclusion VARCHAR(255),
    status     TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 3),
#     draft,published,archived
    published_at DATETIME NULL,
    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE categories
(
    category_id         INT AUTO_INCREMENT PRIMARY KEY,
    parent_id  INT NULL,
    level      INT DEFAULT 1,
    title      VARCHAR(150),
    meta_title VARCHAR(150),
    slug       VARCHAR(150),
    `desc`     TEXT,

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

-- =========================
-- 3. PRODUCT & META & TAG
-- =========================

CREATE TABLE products
(
    product_id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150),
    meta_title   VARCHAR(150),
    slug         VARCHAR(150),
    thumb        VARCHAR(255),
    `desc`       TEXT,
    summary      TEXT,
    type         VARCHAR(150),
    sku          VARCHAR(150),
    price        DECIMAL(12, 2),
    quantity     INT,
    published_at DATETIME,
    status       TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 5),
#   active,out_of_stock,inactive,discontinued,archive
    discount     DECIMAL(12, 2),
    starts_at    DATETIME,
    ends_at      DATETIME,

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE product_metas
(
    meta_id         INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    `key`      VARCHAR(150),
    content    TEXT
);

CREATE TABLE product_categories
(
    product_id  INT,
    category_id INT,
    PRIMARY KEY (product_id, category_id)
);

CREATE TABLE tags
(
    tag_id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(150),
    meta_title VARCHAR(150),
    slug       VARCHAR(150),
    `desc`     TEXT,

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE product_tags
(
    product_id INT,
    tag_id     INT,
    PRIMARY KEY (product_id, tag_id)
);

-- =========================
-- 4. CART & ORDER
-- =========================

CREATE TABLE carts
(
    cart_id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    first_name  VARCHAR(150),
    middle_name VARCHAR(150),
    last_name   VARCHAR(150),
    phone       VARCHAR(20),
    email       VARCHAR(100),
    line1       VARCHAR(255),
    line2       VARCHAR(255),
    city        VARCHAR(255),
    province    VARCHAR(255),
    country     VARCHAR(255),
    status      TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 3),
#   active,checkout_in_progress,checked_out
#     completed, cancel;
    note        VARCHAR(255),

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE cart_items
(
    cart_item_id         INT AUTO_INCREMENT PRIMARY KEY,
    cart_id    INT,
    product_id INT,
    sku        VARCHAR(150),
    is_active  BOOLEAN DEFAULT TRUE,
    price      DECIMAL(12, 2),
    quantity   INT,
    discount   DECIMAL(12, 2),
    note       VARCHAR(255)
);

CREATE TABLE orders
(
    order_id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT,
    subtotal       DECIMAL(12, 2),
    tax            DECIMAL(12, 2),
    shipping       DECIMAL(12, 2),
    total          DECIMAL(12, 2),
    discount_total DECIMAL(12, 2),
    promo          VARCHAR(255),
    discount       DECIMAL(12, 2),
    grand_total    DECIMAL(12, 2),
    first_name     VARCHAR(150),
    middle_name    VARCHAR(150),
    last_name      VARCHAR(150),
    phone          VARCHAR(20),
    email          VARCHAR(100),
    line1          VARCHAR(255),
    line2          VARCHAR(255),
    city           VARCHAR(255),
    province       VARCHAR(255),
    country        VARCHAR(255),
    orders_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    status         TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 8),
#   pending_payment,paid,processing,shipped,delivered,refunded,returned,cancelled
    note           VARCHAR(255),

    version      INT UNSIGNED NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE order_items
(
    order_item_id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT,
    product_id INT,
    sku        VARCHAR(150),
    is_active  BOOLEAN DEFAULT TRUE,
    price      DECIMAL(12, 2),
    quantity   INT,
    discount   DECIMAL(12, 2),
    note       VARCHAR(255)
);

-- =========================
-- 5. TRANSACTION & PARAMETER
-- =========================

CREATE TABLE transactions
(
    transaction_id       INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    amount   DECIMAL(12, 2),
    content  TEXT,
    code     VARCHAR(255),
    type     TINYINT UNSIGNED DEFAULT 1 CHECK (type BETWEEN 1 AND 2),
    mode     VARCHAR(150),
    status   TINYINT UNSIGNED DEFAULT 1 CHECK (status BETWEEN 1 AND 6),
#   initiated,pending,success,failed,cancelled,expired
    version      INT UNSIGNED NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL,
    created_by   INT NULL,
    updated_by   INT NULL
);

CREATE TABLE configs
(
    `key`   VARCHAR(100) PRIMARY KEY,
    `value` VARCHAR(255),
    type  tinyint,
    `desc`         VARCHAR(255),
    updated_at   DATETIME
);


SHOW CREATE TABLE products;
SHOW CREATE TABLE product_metas;
SHOW CREATE TABLE categories;
SHOW CREATE TABLE product_categories;

SHOW CREATE TABLE roles;
SHOW CREATE TABLE user_roles;

SHOW CREATE TABLE orders;


SHOW CREATE TABLE order_items;
SHOW CREATE TABLE carts;
SHOW CREATE TABLE cart_items;
SHOW CREATE TABLE transactions;