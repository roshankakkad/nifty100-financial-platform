-- Query 1
SELECT COUNT(*) AS total_companies FROM companies;

-- Query 2
SELECT COUNT(*) AS total_profit_rows FROM profitandloss;

-- Query 3
SELECT company_id, MAX(sales) AS max_sales
FROM profitandloss
GROUP BY company_id
ORDER BY max_sales DESC
LIMIT 10;

-- Query 4
SELECT company_id, MAX(net_profit) AS max_profit
FROM profitandloss
GROUP BY company_id
ORDER BY max_profit DESC
LIMIT 10;

-- Query 5
SELECT company_id, MAX(total_assets) AS max_assets
FROM balancesheet
GROUP BY company_id
ORDER BY max_assets DESC
LIMIT 10;

-- Query 6
SELECT company_id, AVG(net_cash_flow) AS avg_cashflow
FROM cashflow
GROUP BY company_id
ORDER BY avg_cashflow DESC
LIMIT 10;

-- Query 7
SELECT sector, COUNT(*) AS companies
FROM sectors
GROUP BY sector
ORDER BY companies DESC;

-- Query 8
SELECT COUNT(*) FROM stock_prices;

-- Query 9
SELECT company_id, AVG(close_price) AS avg_price
FROM stock_prices
GROUP BY company_id
ORDER BY avg_price DESC
LIMIT 10;

-- Query 10
SELECT COUNT(*) FROM financial_ratios;