-- script for creating new tables in PostgreSQL
DROP TABLE IF EXISTS chore;
DROP TABLE IF EXISTS person_recipe;
DROP TABLE IF EXISTS recipe_item;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS recipe;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS store;
DROP TABLE IF EXISTS online_api;
DROP TABLE IF EXISTS storage_categories;
DROP TABLE IF EXISTS item_lookup;
DROP TABLE IF EXISTS quantity;

CREATE TABLE quantity (
    quantity_id BIGSERIAL PRIMARY KEY,
    quantity_name VARCHAR(50) NOT NULL
);

CREATE TABLE item_lookup (
    item_lookup_id BIGSERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    barcode VARCHAR(255),
    quantity VARCHAR(255),
    quantity_id INT DEFAULT 1,
    brand VARCHAR(255),
    categories VARCHAR(500),
    energy_kcal_100g DECIMAL(10,3),
    fat_100g DECIMAL(10,3),
    saturated_fat_100g DECIMAL(10,3),
    carbs_100g DECIMAL(10,3),
    sugars_100g DECIMAL(10,3),
    proteins_100g DECIMAL(10,3),
    salt_100g DECIMAL(10,3),
    FOREIGN KEY (quantity_id) REFERENCES quantity(quantity_id)
);

CREATE TABLE item (
    item_id BIGSERIAL PRIMARY KEY,
    item_lookup_id BIGINT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    storage_categories_id BIGINT,
    last_scanned timestamp, 
    FOREIGN KEY (item_lookup_id) REFERENCES item_lookup(item_lookup_id)
);

CREATE TABLE recipe (
    recipe_id BIGSERIAL PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    prep_time DECIMAL(5,2),
    cook_time DECIMAL(5,2),
    instructions VARCHAR(1000),
    video_url VARCHAR(255),
    image bytea
);

CREATE TABLE recipe_item (
    recipe_item_id BIGSERIAL PRIMARY KEY,
    recipe_id INT NOT NULL,
    item_id INT NOT NULL,
    item_quantity DECIMAL(10,2) NOT NULL,
    quantity_id INT NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id),
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (quantity_id) REFERENCES quantity(quantity_id),
    UNIQUE (recipe_id, item_id)
);

CREATE TABLE person (
    person_id BIGSERIAL PRIMARY KEY,
    is_parent BOOLEAN NOT NULL DEFAULT FALSE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(50)
);

CREATE TABLE person_recipe (
    person_recipe_id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL,
    recipe_id INT NOT NULL,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (person_id) REFERENCES person(person_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id),
    UNIQUE (person_id, recipe_id)
);

CREATE TABLE chore (
    chore_id BIGSERIAL PRIMARY KEY,
    chore_num BIGSERIAL,
    description VARCHAR(255) NOT NULL,
    person_id BIGINT NOT NULL,
    frequency VARCHAR(50),
    priority BIGINT,
    FOREIGN KEY (person_id) REFERENCES person(person_id)
);

CREATE TABLE storage_categories (
    storage_categories_id BIGSERIAL PRIMARY KEY,
    storage_category_name VARCHAR(100) NOT NULL,
    quantity_id INT NOT NULL,
    need_refill BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (quantity_id) REFERENCES quantity(quantity_id)
);

INSERT INTO quantity (quantity_name) VALUES
('unit (undefined)'),
('g'),
('cup'),
('tbsp'),
('tsp'),
('lbs'),
('oz'),
('gal'),
('pt'),
('qt'),
('ml'),
('l');

INSERT INTO item_lookup (item_name, description, barcode) VALUES
('Eggland''s Best Large Eggs (12 ct)', 'Eggland''s Best Grade A Large Eggs, 1 dozen', '715141503494'),
('Bertolli Extra Virgin Olive Oil (17 oz)', 'Bertolli extra virgin olive oil, 17 fl oz', '041790001600'),
('Heinz Tomato Ketchup, 20 oz Bottle', 'Heinz tomato ketchup condiment (20 oz squeeze bottle)', '13000006408');
