
from datetime import date, timedelta
from random import Random

from sqlalchemy import text

from app.core.database import engine


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42
rng = Random(SEED)

AS_OF_DATE = date(2026, 11, 24)

BUSINESS_UNITS = [
    ("Technology Services", "India"),
    ("Cloud Solutions", "India"),
    ("Digital Transformation", "US"),
    ("Enterprise Consulting", "UK"),
    ("Data & Analytics", "India"),
]

INDUSTRIES = [
    "Banking",
    "Healthcare",
    "Retail",
    "Manufacturing",
    "Telecommunications",
]

GEOGRAPHIES = ["India", "US", "UK", "Singapore"]

STAGES = [
    "Qualification",
    "Proposal",
    "Negotiation",
    "Closing",
]

FORECAST_CATEGORIES = [
    "Committed",
    "Best Case",
    "Pipeline",
]

TABLES = [
    "billing_snapshots",
    "invoices",
    "billing_work_items",
    "revenue_targets",
    "revenue_records",
    "opportunity_snapshots",
    "opportunities",
    "customers",
    "business_units",
]


# ============================================================
# DATE HELPERS
# ============================================================

def month_end(year: int, month: int) -> date:
    """Return the final calendar day of a month."""

    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)

    return date(year, month + 1, 1) - timedelta(days=1)


def months_back(count: int) -> list[tuple[int, int]]:
    """Return the previous N months, including the current month."""

    year = AS_OF_DATE.year
    month = AS_OF_DATE.month

    result = []

    for _ in range(count):
        result.append((year, month))

        month -= 1

        if month == 0:
            month = 12
            year -= 1

    return list(reversed(result))


def get_snapshot_dates() -> list[date]:
    """
    Generate six snapshot dates:
    five month-end dates and the current as-of date.
    """

    dates = [
        month_end(year, month)
        for year, month in months_back(6)[:-1]
    ]

    dates.append(AS_OF_DATE)

    return dates


# ============================================================
# MAIN DATA GENERATOR
# ============================================================

def build_data(connection):

    # --------------------------------------------------------
    # 0. RESET EXISTING SYNTHETIC DATA
    # --------------------------------------------------------

    print("Resetting existing Flight Deck prototype data...")

    connection.execute(text("""
        TRUNCATE TABLE
            billing_snapshots,
            invoices,
            billing_work_items,
            revenue_targets,
            revenue_records,
            opportunity_snapshots,
            opportunities,
            customers,
            business_units
        RESTART IDENTITY
    """))

    # --------------------------------------------------------
    # 1. BUSINESS UNITS
    # --------------------------------------------------------

    print("Generating business units...")

    connection.execute(
        text("""
            INSERT INTO business_units (
                name,
                geography
            )
            VALUES (
                :name,
                :geography
            )
        """),
        [
            {
                "name": name,
                "geography": geography,
            }
            for name, geography in BUSINESS_UNITS
        ],
    )

    bu_rows = connection.execute(
        text("""
            SELECT id, name, geography
            FROM business_units
            ORDER BY id
        """)
    ).all()

    bu_ids = [row.id for row in bu_rows]

    # --------------------------------------------------------
    # 2. CUSTOMERS
    # --------------------------------------------------------

    print("Generating customers...")

    customers = []

    for i in range(1, 26):

        customers.append({
            "name": f"FD Synthetic Customer {i:03d}",
            "industry": INDUSTRIES[
                (i - 1) % len(INDUSTRIES)
            ],
            "geography": GEOGRAPHIES[
                (i - 1) % len(GEOGRAPHIES)
            ],
        })

    connection.execute(
        text("""
            INSERT INTO customers (
                name,
                industry,
                geography
            )
            VALUES (
                :name,
                :industry,
                :geography
            )
        """),
        customers,
    )

    customer_rows = connection.execute(
        text("""
            SELECT id, name
            FROM customers
            ORDER BY id
        """)
    ).all()

    customer_ids = [row.id for row in customer_rows]

    # --------------------------------------------------------
    # 3. OPPORTUNITIES
    # --------------------------------------------------------

    print("Generating sales opportunities...")

    opportunities = []

    for i in range(1, 101):

        customer_id = rng.choice(customer_ids)
        bu_id = rng.choice(bu_ids)

        stage = rng.choice(STAGES)
        category = rng.choice(FORECAST_CATEGORIES)

        value = rng.randrange(
            500_000,
            15_000_001,
            50_000,
        )

        probability = rng.choice([
            20, 30, 40, 50, 60, 70, 80, 90
        ])

        close_date = AS_OF_DATE + timedelta(
            days=rng.randint(-60, 180)
        )

        status = (
            "closed_won" if i % 15 == 0
            else "closed_lost" if i % 19 == 0
            else "open"
        )

        opportunities.append({
            "opportunity_name": (
                f"FD Synthetic Deal {i:03d}"
            ),
            "customer_id": customer_id,
            "business_unit_id": bu_id,
            "sales_owner": (
                f"Sales Owner {(i % 10) + 1:02d}"
            ),
            "stage": stage,
            "forecast_category": category,
            "opportunity_value": value,
            "probability": probability,
            "expected_close_date": close_date,
            "status": status,
        })

    connection.execute(
        text("""
            INSERT INTO opportunities (
                opportunity_name,
                customer_id,
                business_unit_id,
                sales_owner,
                stage,
                forecast_category,
                opportunity_value,
                probability,
                expected_close_date,
                status
            )
            VALUES (
                :opportunity_name,
                :customer_id,
                :business_unit_id,
                :sales_owner,
                :stage,
                :forecast_category,
                :opportunity_value,
                :probability,
                :expected_close_date,
                :status
            )
        """),
        opportunities,
    )

    opportunity_rows = connection.execute(
        text("""
            SELECT
                id,
                opportunity_value,
                stage,
                forecast_category,
                status
            FROM opportunities
            ORDER BY id
        """)
    ).all()

    # --------------------------------------------------------
    # 4. OPPORTUNITY HISTORICAL SNAPSHOTS
    # --------------------------------------------------------

    print("Generating opportunity snapshots...")

    opportunity_snapshots = []
    snapshot_dates = get_snapshot_dates()

    for opportunity in opportunity_rows:

        current_value = float(
            opportunity.opportunity_value
        )

        current_stage_index = STAGES.index(
            opportunity.stage
        )

        for index, snapshot_date in enumerate(snapshot_dates):

            is_latest = (
                index == len(snapshot_dates) - 1
            )

            if is_latest:

                # Latest snapshot must match current opportunity.
                historical_value = current_value
                historical_stage = opportunity.stage
                historical_status = opportunity.status

            else:

                # Earlier snapshots show simulated deal progression.
                progress = index / (
                    len(snapshot_dates) - 1
                )

                minimum_factor = (
                    0.80 + 0.10 * progress
                )

                maximum_factor = (
                    0.95 + 0.05 * progress
                )

                factor = rng.uniform(
                    minimum_factor,
                    maximum_factor,
                )

                historical_value = round(
                    current_value * factor,
                    2,
                )

                previous_stage_index = max(
                    0,
                    current_stage_index
                    - (len(snapshot_dates) - 1 - index),
                )

                historical_stage = STAGES[
                    previous_stage_index
                ]

                # Opportunities are open before their final
                # current-state snapshot.
                historical_status = "open"

            opportunity_snapshots.append({
                "opportunity_id": opportunity.id,
                "snapshot_date": snapshot_date,
                "stage": historical_stage,
                "forecast_category": (
                    opportunity.forecast_category
                ),
                "opportunity_value": historical_value,
                "status": historical_status,
            })

    connection.execute(
        text("""
            INSERT INTO opportunity_snapshots (
                opportunity_id,
                snapshot_date,
                stage,
                forecast_category,
                opportunity_value,
                status
            )
            VALUES (
                :opportunity_id,
                :snapshot_date,
                :stage,
                :forecast_category,
                :opportunity_value,
                :status
            )
        """),
        opportunity_snapshots,
    )

    # --------------------------------------------------------
    # 5. REVENUE RECORDS AND TARGETS
    # --------------------------------------------------------

    print("Generating monthly revenue records and targets...")

    revenue_records = []
    revenue_targets = []

    revenue_months = months_back(12)

    for year, month in revenue_months:

        for bu_id in bu_ids:

            # Simulated monthly recognized revenue.
            monthly_total = rng.randint(
                8_000_000,
                20_000_000,
            )

            # Monthly target.
            target_amount = rng.randint(
                10_000_000,
                18_000_000,
            )

            revenue_targets.append({
                "business_unit_id": bu_id,
                "target_year": year,
                "target_month": month,
                "target_amount": target_amount,
                "currency": "INR",
            })

            # Divide monthly revenue across ten records.
            weights = [
                rng.randint(1, 100)
                for _ in range(10)
            ]

            weight_total = sum(weights)

            amounts = [
                monthly_total * weight // weight_total
                for weight in weights
            ]

            # Correct rounding remainder so the total
            # exactly matches monthly_total.
            amounts[-1] += (
                monthly_total - sum(amounts)
            )

            for amount in amounts:

                revenue_records.append({
                    "business_unit_id": bu_id,
                    "customer_id": rng.choice(customer_ids),
                    "revenue_date": date(
                        year,
                        month,
                        rng.randint(
                            1,
                            month_end(year, month).day,
                        ),
                    ),
                    "revenue_amount": amount,
                    "revenue_type": "recognized",
                    "currency": "INR",
                })

    connection.execute(
        text("""
            INSERT INTO revenue_records (
                business_unit_id,
                customer_id,
                revenue_date,
                revenue_amount,
                revenue_type,
                currency
            )
            VALUES (
                :business_unit_id,
                :customer_id,
                :revenue_date,
                :revenue_amount,
                :revenue_type,
                :currency
            )
        """),
        revenue_records,
    )

    connection.execute(
        text("""
            INSERT INTO revenue_targets (
                business_unit_id,
                target_year,
                target_month,
                target_amount,
                currency
            )
            VALUES (
                :business_unit_id,
                :target_year,
                :target_month,
                :target_amount,
                :currency
            )
        """),
        revenue_targets,
    )

    # --------------------------------------------------------
    # 6. BILLING WORK ITEMS
    # --------------------------------------------------------

    print("Generating pending billing work items...")

    work_items = []

    for i in range(1, 51):

        work_date = AS_OF_DATE - timedelta(
            days=rng.randint(1, 180)
        )

        work_items.append({
            "customer_id": rng.choice(customer_ids),
            "business_unit_id": rng.choice(bu_ids),
            "work_description": (
                f"Synthetic billable work item {i:03d}"
            ),
            "work_date": work_date,
            "billable_amount": rng.randint(
                50_000,
                1_000_000,
            ),
            "billing_status": (
                "pending" if i % 4 != 0 else "invoiced"
            ),
        })

    connection.execute(
        text("""
            INSERT INTO billing_work_items (
                customer_id,
                business_unit_id,
                work_description,
                work_date,
                billable_amount,
                billing_status
            )
            VALUES (
                :customer_id,
                :business_unit_id,
                :work_description,
                :work_date,
                :billable_amount,
                :billing_status
            )
        """),
        work_items,
    )

    # --------------------------------------------------------
    # 7. INVOICES
    # --------------------------------------------------------

    print("Generating invoices and simulated payment events...")

    invoices = []

    # Keep payment event dates in memory for snapshot generation.
    invoice_payment_dates = {}

    for i in range(1, 201):

        invoice_date = AS_OF_DATE - timedelta(
            days=rng.randint(20, 240)
        )

        due_date = invoice_date + timedelta(days=30)

        amount = rng.randint(
            100_000,
            2_500_000,
        )

        if i % 10 == 0:

            status = "paid"
            paid_amount = amount

        elif i % 7 == 0:

            status = "partially_paid"
            paid_amount = amount // 2

        elif i % 11 == 0:

            status = "draft"
            paid_amount = 0

        else:

            status = "issued"
            paid_amount = 0

        # Simulated payment date for paid/partially paid invoices.
        payment_date = None

        if status in ("paid", "partially_paid"):

            maximum_payment_days = max(
                1,
                (AS_OF_DATE - invoice_date).days,
            )

            payment_date = invoice_date + timedelta(
                days=rng.randint(
                    1,
                    maximum_payment_days,
                )
            )

        invoice_number = f"FD-SYN-{i:05d}"

        invoice_payment_dates[invoice_number] = (
            payment_date
        )

        invoices.append({
            "invoice_number": invoice_number,
            "customer_id": rng.choice(customer_ids),
            "business_unit_id": rng.choice(bu_ids),
            "invoice_date": invoice_date,
            "due_date": due_date,
            "invoice_amount": amount,
            "paid_amount": paid_amount,
            "status": status,
            "currency": "INR",
        })

    connection.execute(
        text("""
            INSERT INTO invoices (
                invoice_number,
                customer_id,
                business_unit_id,
                invoice_date,
                due_date,
                invoice_amount,
                paid_amount,
                status,
                currency
            )
            VALUES (
                :invoice_number,
                :customer_id,
                :business_unit_id,
                :invoice_date,
                :due_date,
                :invoice_amount,
                :paid_amount,
                :status,
                :currency
            )
        """),
        invoices,
    )

    invoice_rows = connection.execute(
        text("""
            SELECT
                id,
                invoice_number,
                invoice_date,
                due_date,
                invoice_amount,
                paid_amount,
                status
            FROM invoices
            ORDER BY id
        """)
    ).all()

    # --------------------------------------------------------
    # 8. BILLING HISTORICAL SNAPSHOTS
    # --------------------------------------------------------

    print("Generating billing snapshots...")

    billing_snapshots = []

    billing_snapshot_dates = get_snapshot_dates()

    for invoice in invoice_rows:

        payment_date = invoice_payment_dates[
            invoice.invoice_number
        ]

        invoice_date = invoice.invoice_date
        due_date = invoice.due_date

        invoice_amount = float(
            invoice.invoice_amount
        )

        paid_amount = float(
            invoice.paid_amount
        )

        for snapshot_date in billing_snapshot_dates:

            # Invoice not issued yet or still in draft.
            if (
                invoice.status == "draft"
                or snapshot_date < invoice_date
            ):

                outstanding = 0

            # Payment has already happened by this snapshot.
            elif (
                payment_date is not None
                and snapshot_date >= payment_date
            ):

                outstanding = (
                    invoice_amount - paid_amount
                )

            # Payment has not happened yet.
            else:

                outstanding = invoice_amount

            # Calculate overdue days only for outstanding invoices.
            days_overdue = (
                max(
                    0,
                    (snapshot_date - due_date).days,
                )
                if outstanding > 0
                else 0
            )

            # Assign ageing bucket.
            if (
                invoice.status == "draft"
                or snapshot_date < invoice_date
            ):

                ageing_bucket = "not_issued"

            elif outstanding == 0:

                ageing_bucket = "paid"

            elif days_overdue == 0:

                ageing_bucket = "current"

            elif days_overdue <= 30:

                ageing_bucket = "1-30"

            elif days_overdue <= 60:

                ageing_bucket = "31-60"

            elif days_overdue <= 90:

                ageing_bucket = "61-90"

            else:

                ageing_bucket = "90+"

            billing_snapshots.append({
                "invoice_id": invoice.id,
                "snapshot_date": snapshot_date,
                "outstanding_amount": outstanding,
                "days_overdue": days_overdue,
                "ageing_bucket": ageing_bucket,
            })

    connection.execute(
        text("""
            INSERT INTO billing_snapshots (
                invoice_id,
                snapshot_date,
                outstanding_amount,
                days_overdue,
                ageing_bucket
            )
            VALUES (
                :invoice_id,
                :snapshot_date,
                :outstanding_amount,
                :days_overdue,
                :ageing_bucket
            )
        """),
        billing_snapshots,
    )

    # --------------------------------------------------------
    # 9. RETURN GENERATED RECORD COUNTS
    # --------------------------------------------------------

    return {
        "business_units": len(BUSINESS_UNITS),
        "customers": len(customers),
        "opportunities": len(opportunities),
        "opportunity_snapshots": len(opportunity_snapshots),
        "revenue_records": len(revenue_records),
        "revenue_targets": len(revenue_targets),
        "billing_work_items": len(work_items),
        "invoices": len(invoices),
        "billing_snapshots": len(billing_snapshots),
    }


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("FLIGHT DECK SYNTHETIC DATA GENERATOR")
    print("=" * 55)

    print(f"Random seed: {SEED}")
    print(f"Data as-of date: {AS_OF_DATE}")

    # All deletes and inserts happen in one transaction.
    # If generation fails, the transaction rolls back.
    with engine.begin() as connection:
        counts = build_data(connection)

    print("\nSynthetic Flight Deck dataset created successfully!")
    print("-" * 55)

    total_records = 0

    for table, count in counts.items():
        print(f"{table:30} {count:>8,}")
        total_records += count

    print("-" * 55)
    print(f"{'TOTAL RECORDS':30} {total_records:>8,}")

    print("\nAll financial amounts are synthetic INR values.")
    print("Revenue monthly allocations reconcile exactly.")
    print("Historical snapshots generated for Sales and Billing.")
    print("Existing synthetic data was replaced transactionally.")
