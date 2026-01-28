-- script for creating new tables in PostgreSQL
CREATE TABLE item_lookup (
    item_lookup_id BIGSERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    barcode VARCHAR(12)
);

CREATE TABLE item (
    item_id SERIAL PRIMARY KEY,
    item_lookup_id BIGINT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_item_item_lookup
        FOREIGN KEY (item_lookup_id)
        REFERENCES item_lookup(item_lookup_id)
);

CREATE TABLE recipe (
    recipe_id SERIAL PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE recipe_item (
    recipe_item_id SERIAL PRIMARY KEY,
    recipe_id INT NOT NULL,
    item_id INT NOT NULL,
    item_quantity DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_recipe_item_recipe
        FOREIGN KEY (recipe_id)
        REFERENCES recipe(recipe_id),

    CONSTRAINT fk_recipe_item_item
        FOREIGN KEY (item_id)
        REFERENCES item(item_id),

    CONSTRAINT uq_recipe_item UNIQUE (recipe_id, item_id)
);

INSERT INTO item_lookup (item_name, description, barcode) VALUES
('Eggland''s Best Large Eggs (12 ct)', 'Eggland''s Best Grade A Large Eggs, 1 dozen', '715141503494'),
('Bertolli Extra Virgin Olive Oil (17 oz)', 'Bertolli extra virgin olive oil, 17 fl oz', '041790001600'),
('Heinz Tomato Ketchup, 20 oz Bottle', 'Heinz tomato ketchup condiment (20 oz squeeze bottle)', '13000006408');

INSERT INTO item (item_lookup_id, quantity) VALUES
(1,12),
(2,1),
(3,2);