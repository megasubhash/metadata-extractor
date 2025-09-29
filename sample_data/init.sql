-- Sample PostgreSQL schema and data for testing
CREATE SCHEMA IF NOT EXISTS public;

DROP TABLE IF EXISTS public.customers;
CREATE TABLE public.customers (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    signup_date DATE,
    country TEXT
);
COMMENT ON TABLE public.customers IS 'Customer master data';
COMMENT ON COLUMN public.customers.name IS 'Full name of the customer';
COMMENT ON COLUMN public.customers.email IS 'Email address of the customer';

DROP TABLE IF EXISTS public.orders;
CREATE TABLE public.orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES public.customers(id),
    product TEXT,
    quantity INT,
    order_date DATE
);
COMMENT ON TABLE public.orders IS 'Orders placed by customers';
COMMENT ON COLUMN public.orders.customer_id IS 'FK to customers.id';

INSERT INTO public.customers (name, email, signup_date, country) VALUES
('Alice Johnson', 'alice@example.com', '2024-01-15', 'US'),
('Bob Smith', NULL, '2024-02-20', 'IN'),
('Charlie Brown', 'charlie@example.com', NULL, 'UK'),
('Dana Lee', 'dana@example.com', '2024-03-05', 'US');

INSERT INTO public.orders (customer_id, product, quantity, order_date) VALUES
(1, 'Widget', 3, '2024-03-10'),
(1, 'Gadget', 1, '2024-04-01'),
(2, 'Widget', 2, '2024-03-22'),
(3, 'Thingamajig', 5, NULL);
