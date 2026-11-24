
from sqlalchemy import text
from sqlalchemy.orm import Session


QUERIES = {
    "SAL-001": {
        "question": "What is our current sales pipeline?",
        "sql": """
            SELECT
                COUNT(*) AS opportunity_count,
                COALESCE(SUM(opportunity_value), 0) AS pipeline_value
            FROM opportunities
            WHERE status = 'open'
        """
    },

    "SAL-004": {
        "question": "What are the top 10 deals by value?",
        "sql": """
            SELECT
                o.opportunity_name,
                c.name AS customer_name,
                o.opportunity_value,
                o.stage,
                o.sales_owner
            FROM opportunities o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.status = 'open'
            ORDER BY o.opportunity_value DESC
            LIMIT 10
        """
    },

    "REV-001": {
        "question": "What is our total revenue this quarter?",
        "sql": """
            SELECT
                COALESCE(SUM(revenue_amount), 0) AS total_revenue
            FROM revenue_records
            WHERE revenue_type = 'recognized'
              AND revenue_date >= date_trunc('quarter', CURRENT_DATE)
              AND revenue_date < date_trunc('quarter', CURRENT_DATE)
                                  + INTERVAL '3 months'
        """
    },

    "REV-004": {
        "question": "What is our monthly revenue trend over the last 12 months?",
        "sql": """
            SELECT
                date_trunc('month', revenue_date)::date AS revenue_month,
                SUM(revenue_amount) AS total_revenue
            FROM revenue_records
            WHERE revenue_type = 'recognized'
              AND revenue_date >= date_trunc('month', CURRENT_DATE)
                                  - INTERVAL '11 months'
            GROUP BY 1
            ORDER BY 1
        """
    },

    "BIL-001": {
        "question": "How much billing is pending?",
        "sql": """
            SELECT
                COUNT(*) AS pending_work_items,
                COALESCE(SUM(billable_amount), 0) AS pending_billing
            FROM billing_work_items
            WHERE billing_status = 'pending'
        """
    },

    "BIL-002": {
        "question": "Which customers have the highest overdue billing?",
        "sql": """
            SELECT
                c.name AS customer_name,
                SUM(bs.outstanding_amount) AS overdue_amount
            FROM billing_snapshots bs
            JOIN invoices i ON i.id = bs.invoice_id
            JOIN customers c ON c.id = i.customer_id
            WHERE bs.snapshot_date = (
                SELECT MAX(snapshot_date)
                FROM billing_snapshots
            )
              AND bs.days_overdue > 0
              AND bs.outstanding_amount > 0
            GROUP BY c.id, c.name
            ORDER BY overdue_amount DESC
            LIMIT 10
        """
    }
}


def execute_query(db: Session, query_id: str):
    query = QUERIES.get(query_id)

    if not query:
        return None

    result = db.execute(text(query["sql"]))

    return {
        "query_id": query_id,
        "question": query["question"],
        "data": [dict(row) for row in result.mappings().all()]
    }
