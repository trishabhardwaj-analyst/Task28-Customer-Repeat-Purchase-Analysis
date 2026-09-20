# Task 28 — Customer Repeat Purchase Analysis

## 📊 Project Overview

This project analyzes customer repeat-purchase behavior and identifies customer segments for retention and loyalty analysis.

**Task:** 28  
**Title:** Customer Repeat Purchase Analysis  
**Track:** Data Analytics  
**Tools:** Python, SQL  
**Dataset:** Online Retail II

The analysis focuses on:

- Measuring repeat purchase rate
- Identifying repeat customers
- Comparing first-time and repeat purchases
- Comparing first-time and repeat AOV
- Analyzing customer purchase frequency
- Performing RFM customer segmentation
- Identifying important customer segments
- Generating business insights and retention recommendations

---

## 🎯 Objective

The main objective is to understand customer loyalty and repeat-purchase behavior using historical transaction data.

The analysis answers the following questions:

1. How many customers purchase more than once?
2. What is the repeat purchase rate?
3. How many customers are one-time buyers?
4. How does first-time order AOV compare with repeat-order AOV?
5. How frequently do customers purchase?
6. Which customer segments contribute the most revenue?
7. What retention strategies can be developed from the analysis?

---

# 📂 Dataset

## Online Retail II

The project uses the **Online Retail II** dataset from the UCI Machine Learning Repository.

**Dataset Source:**  
https://archive.ics.uci.edu/dataset/502/online+retail+ii

**DOI:**  
https://doi.org/10.24432/C5CG6D

The dataset contains transactional records from a UK-based registered non-store online retailer covering transactions from **December 2009 to December 2011**.

The dataset contains two worksheets:

- `Year 2009-2010`
- `Year 2010-2011`

### Important Columns

| Column | Description |
|---|---|
| Invoice / InvoiceNo | Unique invoice/order identifier |
| StockCode | Product identifier |
| Description | Product description |
| Quantity | Number of units purchased |
| InvoiceDate | Transaction date and time |
| Price / UnitPrice | Unit price in GBP |
| Customer ID | Customer identifier |
| Country | Customer country |

---

# 📥 Dataset Setup

The raw dataset is not included in this GitHub repository because the Excel workbook is large.

Download the dataset from:

https://archive.ics.uci.edu/dataset/502/online+retail+ii

After downloading the Excel workbook, rename it to:

```text
online_retail_II.xlsx
