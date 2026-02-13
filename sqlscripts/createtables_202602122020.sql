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
    description VARCHAR(255) NOT NULL,
    person_id BIGINT NOT NULL,
    frequency VARCHAR(50),
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

-- IMPORTANT!!! Select everything above this and run the selected scripts
-- Then, after downloading the products_filtered file, run
-- psql -d homeappdb -U postgres -h localhost -c "\COPY item_lookup (barcode,item_name,brand,quantity,categories,energy_kcal_100g,fat_100g,saturated_fat_100g,carbs_100g,sugars_100g,proteins_100g,salt_100g,quantity_id) FROM 'C:\Users\perri\Downloads\products_filtered.csv' DELIMITER ',' CSV HEADER ENCODING 'Latin1';"
-- Then select everything below this and run the selected scripts to populate the item table and other related tables

INSERT INTO item (item_lookup_id, quantity) VALUES
(1,12),
(2,1),
(3,2),
(4,6),
(5,2),
(6,2),
(7,2),
(8,2),
(9,2),
(10,2);

INSERT INTO recipe (recipe_name, prep_time, cook_time, instructions, video_url, image) VALUES
('Scrambled Eggs', 5, 10, 'step 1 Crack the eggs into a bowl, add a splash of milk, salt, and pepper, then whisk until fully combined. Heat butter in a nonstick frying pan over medium-low heat until melted but not browned. step 2 Pour in the eggs and let them sit for 20–30 seconds, then gently stir with a spatula, pushing the eggs from the edges toward the center. Continue stirring slowly until soft curds form and the eggs are just set but still slightly creamy. Remove from heat immediately and serve warm.', '', ''),
('Garlic Chicken', 15, 30, 'step 1 Season chicken breasts with salt, pepper, and paprika. Heat olive oil in a large skillet over medium heat, then add the chicken and cook for 5–7 mins per side until golden brown and cooked through. Remove from pan and set aside. step 2 In the same pan, add minced garlic and cook for 1 min until fragrant. Stir in chicken broth and a squeeze of lemon juice, scraping up browned bits, then simmer for 3–4 mins until slightly reduced. Return chicken to the pan, spoon sauce over the top, and cook for 2 mins more before serving.', '', ''),
('Pancakes', 10, 15, 'step 1 In a bowl whisk together flour, sugar, baking powder, and salt. In another bowl mix milk, egg, and melted butter, then pour the wet ingredients into the dry and stir until just combined. Heat a lightly greased skillet over medium heat. step 2 Pour batter onto the skillet in small rounds and cook for 2–3 mins until bubbles form on the surface. Flip and cook for another 1–2 mins until golden brown. Serve warm with syrup or toppings of choice.', '', ''),
('Waffles', 10, 10, 'step 1 Preheat the waffle iron and lightly grease if needed. In a bowl mix flour, baking powder, sugar, and salt. In another bowl whisk together milk, eggs, melted butter, and vanilla, then combine with the dry ingredients until smooth. step 2 Pour batter into the waffle iron and cook according to manufacturer instructions until golden and crisp. Carefully remove and serve immediately with fruit, syrup, or whipped cream.', '', ''),
('Steak Dinner', 30, 40, 'step 1 Remove steak from the fridge 20–30 mins before cooking and season generously with salt and pepper. Heat a heavy skillet over high heat with a little oil until very hot, then add the steak and sear for 3–4 mins per side for medium-rare, adjusting time for desired doneness. step 2 Add butter, garlic, and fresh herbs to the pan and spoon the melted butter over the steak for 1–2 mins. Remove from heat and let rest for 5–10 mins before slicing. Serve with mashed potatoes and steamed vegetables.', '', ''),
('Fruit Salad', 10, 10, 'step 1 Wash and chop a variety of fresh fruits such as strawberries, blueberries, pineapple, grapes, and melon into bite-sized pieces. Place them in a large mixing bowl. step 2 Drizzle with a little honey and fresh lemon or lime juice, then gently toss to combine. Chill for at least 30 mins before serving for best flavor.', '', ''),
('Spaghetti', 20, 20, 'step 1 Bring a large pot of salted water to the boil, add spaghetti, and cook according to package instructions until al dente. Meanwhile heat olive oil in a pan over medium heat and sauté diced onion and minced garlic until softened. Add ground beef if using and cook until browned, then stir in tomato sauce and Italian seasoning and simmer for 10–15 mins. step 2 Drain the pasta and toss with the sauce until evenly coated. Serve hot topped with grated Parmesan and fresh basil.', '', ''),
('Grilled Chicken', 30, 20, 'step 1 Preheat grill to medium-high heat and lightly oil the grates. Season chicken breasts with olive oil, salt, pepper, and preferred spices or marinade. step 2 Grill the chicken for 6–8 mins per side, turning once, until internal temperature reaches 165°F. Remove from grill and let rest for 5 mins before slicing and serving.', '', ''),
('Chipotle Hamburgers', 20, 20, 'step 1 In a bowl combine ground beef with minced chipotle peppers in adobo sauce, salt, pepper, and a little garlic powder, then form into patties. Preheat grill or skillet to medium-high heat and lightly oil the surface. step 2 Cook patties for 4–5 mins per side until desired doneness, adding cheese in the final minute if desired. Toast burger buns lightly, then assemble with lettuce, tomato, onion, and chipotle mayo before serving.', '', ''),
('Chicken Noodle Soup', 30, 50, 'step 1 Heat olive oil in a large pot over medium heat, then sauté diced onion, carrots, and celery for 5 mins until softened. Add minced garlic and cook for 1 min, then pour in chicken broth and bring to a gentle boil. step 2 Add diced cooked chicken and egg noodles and simmer for 8–10 mins until noodles are tender. Season with salt, pepper, and fresh parsley, then serve hot.', '', '')
--('Seafood rice', 15, 15, 'step 1 Heat the oil in a deep frying pan, then soften the leek for 5 mins without browning. Add the chorizo and fry until it releases its oils. Stir in the turmeric and rice until coated by the oils, then pour in the stock. Bring to the boil, then simmer for 15 mins, stirring occasionally. step 2 Tip in the peas and cook for 5 mins, then stir in the seafood to heat through for a final 1-2 mins cooking or until rice is cooked. Check for seasoning and serve immediately with lemon wedges.', 'https://www.youtube.com/watch?v=Dr8Nsod20yg', 'https://www.themealdb.com/images/media/meals/5r5rvx1763287943.jpg')
;

INSERT INTO recipe_item (recipe_id, item_id, item_quantity, quantity_id) VALUES
(1, 1, 3, 1),
(1, 2, 1, 5),
(2, 3, 2, 5),
(2, 1, 1, 3),
(3, 2, 2, 2),
(3, 3, 1, 2),
(4, 1, 1, 7),
(4, 3, 1, 2),
(5, 2, 1, 2),
(5, 3, 1, 2),
(6, 3, 1, 2),
(7, 3, 1, 2);

INSERT INTO person (is_parent, first_name, last_name, date_of_birth, gender) VALUES
(TRUE, 'Nick', 'Perrin', '1999-04-15', 'M'),
(TRUE, 'Sarah', 'Perrin', '2000-06-20', 'F'),
(FALSE, 'Alex', 'Smith', '2010-09-01', 'M');

INSERT INTO person_recipe (person_id, recipe_id, is_favorite) VALUES
(1, 1, TRUE),
(1, 3, TRUE),
(2, 2, FALSE);

INSERT INTO chore (description, person_id, frequency) VALUES
('Wash dishes', 1, 'Daily'),
('Take out trash', 2, 'Weekly'),
('Clean room', 3, 'Weekly'),
('Vacuum', 3, 'Weekly'),
('Mop', 2, 'Weekly'),
('Dust', 1, 'Weekly'),
('Clean room', 2, 'Weekly'),
('Walk dog', 3, 'Weekly'),
('Mow lawn', 3, 'Weekly'),
('Laundry', 3, 'Weekly');

INSERT INTO storage_categories (storage_category_name, quantity_id, need_refill) VALUES
('Kitchen Pantry', 2, FALSE),
('Refrigerator', 1, FALSE),
('Freezer', 5, TRUE),
('Garage Storage', 7, FALSE);