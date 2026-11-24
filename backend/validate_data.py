
from sqlalchemy import text
from app.core.database import engine

checks = {
    "business_units": """
        SELECT COUNT(*) FROM business_units
    """,
    "customers": """
        SELECT COUNT(*) FROM customers
    """,
    "opportunities": """
        SELECT COUNT(*) FROM opportunities
    """,
    "opportunity_snapshots": """
        SELECT COUNT(*) FROM opportunity_snapshots
    """,
    "revenue_records": """
        SELECT COUNT(*) FROM revenue_records
    """,
    "revenue_targets": """
        SELECT COUNT(*) FROM revenue_targets
    """,
    "billing_work_items": """
        SELECT COUNT(*) FROM billing_work_items
    """,
    "invoices": """
        SELECT COUNT(*) FROM invoices
    """,
    "billing_snapshots": """
        SELECT COUNT(*) FROM billing_snapshots
    """,
}

with engine.connect() as connection:
    print("\nFLIGHT DECK DATA QUALITY REPORT")
    print("=" * 45)

    for table, query in checks.items():
        count = connection.execute(text(query)).scalar_one()
        print(f"{table:25} {count:>6,}")

    opportunity_check = connection.execute(text("""
        SELECT COUNT(*)
        FROM opportunities o
        LEFT JOIN (
            SELECT opportunity_id, COUNT(*) AS snapshot_count
            FROM opportunity_snapshots
            GROUP BY opportunity_id
        ) s ON s.opportunity_id = o.id
        WHERE COALESCE(s.snapshot_count, 0) != 6
    """)).scalar_one()

    invoice_check = connection.execute(text("""
        SELECT COUNT(*)
        FROM invoices i
        LEFT JOIN (
            SELECT invoice_id, COUNT(*) AS snapshot_count
            FROM billing_snapshots
            GROUP BY invoice_id
        ) s ON s.invoice_id = i.id
        WHERE COALESCE(s.snapshot_count, 0) != 6
    """)).scalar_one()

    invalid_invoices = connection.execute(text("""
        SELECT COUNT(*)
        FROM invoices
        WHERE paid_amount > invoice_amount
           OR paid_amount < 0
           OR invoice_amount < 0
    """)).scalar_one()

    invalid_revenue = connection.execute(text("""
        SELECT COUNT(*)
        FROM revenue_records
        WHERE revenue_amount < 0
           OR currency != 'INR'
    """)).scalar_one()

    revenue_months = connection.execute(text("""
        SELECT COUNT(DISTINCT date_trunc('month', revenue_date))
        FROM revenue_records
    """)).scalar_one()

    print("\nQUALITY CHECKS")
    print("=" * 45)
    print("Opportunities without six snapshots:", opportunity_check)
    print("Invoices without six snapshots:", invoice_check)
    print("Invalid invoice balances:", invalid_invoices)
    print("Invalid revenue records:", invalid_revenue)
    print("Distinct revenue months:", revenue_months)
