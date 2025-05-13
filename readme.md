CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    age INT,
    weight DECIMAL(5, 2),
    height DECIMAL(5, 2),
    gender VARCHAR(10),
    training_intensity VARCHAR(50),
    training_goal VARCHAR(20),
    is_subscribed BOOLEAN DEFAULT FALSE,
    subscription_plan TEXT DEFAULT 'none'
);


CREATE TABLE calorie_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    food_name VARCHAR(255),
    calories NUMERIC(5,2),
    protein NUMERIC(5,2),
    carbs NUMERIC(5,2),
    fats NUMERIC(5,2),
    log_date DATE
);