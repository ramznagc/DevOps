-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on name for faster searches
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Insert sample data
INSERT INTO products (name, description, price, stock) VALUES
    ('Laptop', 'High-performance laptop with 16GB RAM', 1299.99, 15),
    ('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 50),
    ('USB-C Hub', '7-in-1 USB-C hub with HDMI and card reader', 49.99, 30),
    ('Mechanical Keyboard', 'RGB mechanical keyboard with blue switches', 89.99, 20),
    ('Monitor 27"', '4K UHD monitor with HDR support', 399.99, 10),
    ('Webcam HD', '1080p webcam with built-in microphone', 79.99, 25),
    ('Laptop Stand', 'Adjustable aluminum laptop stand', 39.99, 40),
    ('Headphones', 'Noise-cancelling wireless headphones', 199.99, 18),
    ('External SSD', '1TB portable external SSD', 129.99, 35),
    ('Phone Stand', 'Adjustable phone stand for desk', 19.99, 60);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE
    ON products FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();