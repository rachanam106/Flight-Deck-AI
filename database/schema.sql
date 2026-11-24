
-- Flight Deck: Synthetic Business Data Schema
-- All financial amounts are stored in INR.
-- Prototype schema; business definitions require validation.

CREATE TABLE IF NOT EXISTS business_units (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    geography VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    industry VARCHAR(100),
    geography VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS opportunities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    opportunity_name VARCHAR(200) NOT NULL,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    business_unit_id BIGINT NOT NULL REFERENCES business_units(id),
    sales_owner VARCHAR(120) NOT NULL,
    stage VARCHAR(40) NOT NULL,
    forecast_category VARCHAR(40) NOT NULL,
    opportunity_value NUMERIC(16,2) NOT NULL CHECK (opportunity_value >= 0),
    probability NUMERIC(5,2) NOT NULL CHECK (probability BETWEEN 0 AND 100),
    expected_close_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS opportunity_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    opportunity_id BIGINT NOT NULL REFERENCES opportunities(id),
    snapshot_date DATE NOT NULL,
    stage VARCHAR(40) NOT NULL,
    forecast_category VARCHAR(40) NOT NULL,
    opportunity_value NUMERIC(16,2) NOT NULL CHECK (opportunity_value >= 0),
    status VARCHAR(30) NOT NULL,
    UNIQUE (opportunity_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS revenue_records (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_unit_id BIGINT NOT NULL REFERENCES business_units(id),
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    revenue_date DATE NOT NULL,
    revenue_amount NUMERIC(16,2) NOT NULL CHECK (revenue_amount >= 0),
    revenue_type VARCHAR(40) NOT NULL DEFAULT 'recognized',
    currency CHAR(3) NOT NULL DEFAULT 'INR'
        CHECK (currency = 'INR'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS revenue_targets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_unit_id BIGINT NOT NULL REFERENCES business_units(id),
    target_year INTEGER NOT NULL,
    target_month INTEGER NOT NULL CHECK (target_month BETWEEN 1 AND 12),
    target_amount NUMERIC(16,2) NOT NULL CHECK (target_amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR'
        CHECK (currency = 'INR'),
    UNIQUE (business_unit_id, target_year, target_month)
);

-- Work completed but not yet invoiced.
-- This is deliberately separate from overdue invoices.
CREATE TABLE IF NOT EXISTS billing_work_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    business_unit_id BIGINT NOT NULL REFERENCES business_units(id),
    work_description VARCHAR(200) NOT NULL,
    work_date DATE NOT NULL,
    billable_amount NUMERIC(16,2) NOT NULL CHECK (billable_amount >= 0),
    billing_status VARCHAR(30) NOT NULL
        CHECK (billing_status IN ('pending', 'invoiced', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    business_unit_id BIGINT NOT NULL REFERENCES business_units(id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    invoice_amount NUMERIC(16,2) NOT NULL CHECK (invoice_amount >= 0),
    paid_amount NUMERIC(16,2) NOT NULL DEFAULT 0
        CHECK (paid_amount >= 0),
    status VARCHAR(30) NOT NULL
        CHECK (status IN ('draft', 'issued', 'partially_paid', 'paid', 'cancelled')),
    currency CHAR(3) NOT NULL DEFAULT 'INR'
        CHECK (currency = 'INR'),
    CHECK (paid_amount <= invoice_amount),
    CHECK (due_date >= invoice_date)
);

CREATE TABLE IF NOT EXISTS billing_snapshots (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES invoices(id),
    snapshot_date DATE NOT NULL,
    outstanding_amount NUMERIC(16,2) NOT NULL
        CHECK (outstanding_amount >= 0),
    days_overdue INTEGER NOT NULL DEFAULT 0
        CHECK (days_overdue >= 0),
    ageing_bucket VARCHAR(20) NOT NULL,
    UNIQUE (invoice_id, snapshot_date)
);

-- Indexes for common query filters and joins.
CREATE INDEX IF NOT EXISTS idx_opportunities_bu_status
    ON opportunities (business_unit_id, status);

CREATE INDEX IF NOT EXISTS idx_opportunities_close_date
    ON opportunities (expected_close_date);

CREATE INDEX IF NOT EXISTS idx_opportunity_snapshots_date
    ON opportunity_snapshots (snapshot_date);

CREATE INDEX IF NOT EXISTS idx_revenue_date_bu
    ON revenue_records (revenue_date, business_unit_id);

CREATE INDEX IF NOT EXISTS idx_revenue_targets_period
    ON revenue_targets (target_year, target_month);

CREATE INDEX IF NOT EXISTS idx_work_items_status
    ON billing_work_items (billing_status, work_date);

CREATE INDEX IF NOT EXISTS idx_invoices_due_status
    ON invoices (due_date, status);

CREATE INDEX IF NOT EXISTS idx_billing_snapshots_date
    ON billing_snapshots (snapshot_date);
