-- TASK 28: Customer Repeat Purchase Analysis
-- SQLite / DBeaver compatible
--
-- Run the Python script first. It creates:
-- outputs/clean_orders.csv
-- outputs/customer_repeat_metrics.csv
-- outputs/repeat_rate_calculated.csv
-- outputs/first_time_vs_repeat_orders.csv
-- outputs/purchase_frequency_segments.csv
-- outputs/rfm_customer_segments.csv
--
-- Import clean_orders.csv as table: clean_orders
-- Import customer_repeat_metrics.csv as table: customer_repeat_metrics

-- 1. Overall repeat purchase rate
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN TotalOrders >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
    SUM(CASE WHEN TotalOrders = 1 THEN 1 ELSE 0 END) AS one_time_customers,
    ROUND(
        100.0 * SUM(CASE WHEN TotalOrders >= 2 THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS repeat_purchase_rate_pct
FROM customer_repeat_metrics;

-- 2. First-time vs repeat orders
WITH ordered AS (
    SELECT
        CustomerID,
        InvoiceNo,
        OrderDate,
        OrderRevenue,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerID
            ORDER BY OrderDate, InvoiceNo
        ) AS order_number
    FROM clean_orders
)
SELECT
    CASE
        WHEN order_number = 1 THEN 'First-Time Order'
        ELSE 'Repeat Order'
    END AS order_type,
    COUNT(DISTINCT InvoiceNo) AS orders,
    COUNT(DISTINCT CustomerID) AS customers,
    ROUND(SUM(OrderRevenue), 2) AS revenue,
    ROUND(AVG(OrderRevenue), 2) AS avg_order_value
FROM ordered
GROUP BY order_type
ORDER BY order_type;

-- 3. Customer frequency buckets
SELECT
    CASE
        WHEN TotalOrders = 1 THEN '1 order'
        WHEN TotalOrders BETWEEN 2 AND 3 THEN '2-3 orders'
        WHEN TotalOrders BETWEEN 4 AND 6 THEN '4-6 orders'
        WHEN TotalOrders BETWEEN 7 AND 12 THEN '7-12 orders'
        ELSE '13+ orders'
    END AS frequency_bucket,
    COUNT(*) AS customers,
    ROUND(SUM(TotalRevenue), 2) AS revenue,
    ROUND(AVG(TotalOrders), 2) AS avg_orders
FROM customer_repeat_metrics
GROUP BY frequency_bucket
ORDER BY
    CASE frequency_bucket
        WHEN '1 order' THEN 1
        WHEN '2-3 orders' THEN 2
        WHEN '4-6 orders' THEN 3
        WHEN '7-12 orders' THEN 4
        WHEN '13+ orders' THEN 5
    END;

-- 4. Customer-level first and latest purchase
SELECT
    CustomerID,
    TotalOrders,
    FirstPurchase,
    LastPurchase,
    TotalRevenue,
    AOV,
    CASE
        WHEN TotalOrders >= 2 THEN 'Repeat Buyer'
        ELSE 'One-Time Buyer'
    END AS repeat_segment
FROM customer_repeat_metrics
ORDER BY TotalRevenue DESC;

-- 5. Monthly new vs returning order revenue
WITH ordered AS (
    SELECT
        CustomerID,
        InvoiceNo,
        OrderDate,
        OrderRevenue,
        ROW_NUMBER() OVER (
            PARTITION BY CustomerID
            ORDER BY OrderDate, InvoiceNo
        ) AS order_number
    FROM clean_orders
)
SELECT
    strftime('%Y-%m', OrderDate) AS year_month,
    CASE
        WHEN order_number = 1 THEN 'First-Time Order'
        ELSE 'Repeat Order'
    END AS order_type,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(OrderRevenue), 2) AS revenue
FROM ordered
GROUP BY year_month, order_type
ORDER BY year_month, order_type;
