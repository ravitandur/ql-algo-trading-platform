# Algo Trading Platform MVP - Product Requirements

## 1. Overview
We are building an **AWS-native Algo Trading Platform** where users can:
- Define and execute **options strategies** (via baskets & strategies).
- Manage **orders, positions, and brokers**.
- Use a **marketplace** of pre-defined baskets (by admin) or define their own.
- Execute trades automatically via **EventBridge triggers** and **broker APIs**.

The platform will initially support **Zerodha** as the broker and data source, with plans to extend to Angel, Finvasia, and Zebu.
Design the application 

---

## 2. Functional Requirements

### 2.1 User Management & Authentication
- Use **AWS Cognito** for authentication & user management.
- Each user can:
    - Define baskets and strategies.
    - Subscribe to admin-created baskets.
    - Execute strategies across multiple brokers.

### 2.2 Basket & Strategy Management
- **Basket**:
    - Contains one or more strategies.
    - Can be defined by **admin** (marketplace) or **user** (custom).
- **Strategy**:
    - Belongs to a basket.
    - Has one or more **legs**.
    - Configurable with:
        - Entry time.
        - Exit time.
        - Weekdays (Mon–Fri selection).
        - Days to Expiry (DTE filter).
        - Transaction type (BUY/SELL).
    - Can be **time-based** or **indicator-based**.

### 2.3 Strategy Execution
- Execution is driven by **EventBridge schedules** (per strategy).
- At strategy entry time:
    - EventBridge triggers Lambda.
    - Lambda evaluates entry conditions (time, weekday, DTE, indicators).
    - If conditions met → send order request to broker API.
- At strategy exit time:
    - EventBridge triggers Lambda.
    - Lambda evaluates exit conditions.
    - If conditions met → exit order.

### 2.4 Broker Integration
- Start with **Zerodha** for both:
    - **Market data ingestion** (quotes, option chains).
    - **Order execution** (place, modify, cancel orders).
- Extend later to **Angel, Finvasia, Zebu**.
- Users can link multiple broker accounts and run same strategy across them.

### 2.5 Orders & Positions
- Track **orders & positions** in **DynamoDB**:
    - `orders` table → order_id, user_id, basket_id, strategy_id, broker, status.
    - `positions` table → position_id, user_id, strategy_id, symbol, qty, avg_price, P&L.
- Update status from broker webhooks or polling.

### 2.6 Marketplace
- **Admin** can define option baskets in marketplace.
- **Users** can:
    - Subscribe to marketplace baskets.
    - Define their own baskets.

---

## 3. Non-Functional Requirements
- Built in **Python**.
- Infra managed with **AWS CDK** Python.
- Services: **Lambda, DynamoDB, EventBridge, S3, Fargate, SQS**.
- Data stored in **Parquet** (for reporting/logging).
- Modular architecture, best practices (CQRS + event-driven).
- Orchastration : **Step Functions**
- Start with **MVP scope** (no backtesting yet).

---

## 4. Example Flow

### Basket/Strategy Setup
1. User creates basket "BankNifty Weekly Straddle".
2. Adds strategy:
    - Entry: 9:30 AM IST, weekdays Mon/Wed/Fri, DTE = 0 (expiry day).
    - Exit: 3:15 PM IST.
    - Transaction type: SELL.
    - Legs:
        - SELL 1 lot ATM CE.
        - SELL 1 lot ATM PE.

### Execution Flow
1. At 9:30 → EventBridge triggers Lambda for strategy.
2. Lambda checks weekday + DTE.
3. If valid → calls Zerodha API to place SELL orders.
4. Orders stored in `orders` table.
5. Positions stored in `positions` table.
6. At 3:15 → EventBridge triggers exit Lambda.
7. Exit orders executed, positions updated.

---

## 5. Event Payload Design

Each EventBridge event payload should include:
```json
{
  "user_id": "U123",
  "basket_id": "B456",
  "strategy_id": "S789",
  "transaction_type": "ENTRY/EXIT",
  "entry_time": "09:30",
  "exit_time": "15:15",
  "weekdays": ["MON", "WED", "FRI"],
  "dte": 0
}
