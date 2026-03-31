"""
ChromaDB-based RAG system for database schema understanding.
Indexes table schemas, column descriptions, relationships, and sample queries.
"""

import json
import chromadb
from chromadb.config import Settings
from database import get_schema_info
import os


CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


def get_chroma_client():
    """Get ChromaDB client with persistence."""
    return chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=CHROMA_PERSIST_DIR,
        anonymized_telemetry=False
    ))


def build_schema_documents() -> list[dict]:
    """Convert database schema into documents for RAG indexing."""
    schema_info = get_schema_info()
    documents = []

    for table in schema_info:
        table_name = table["table_name"]
        columns = table["columns"]
        row_count = table["row_count"]

        # 1. Table overview document
        col_descriptions = []
        for col in columns:
            pk = " (PRIMARY KEY)" if col["primary_key"] else ""
            nullable = " (nullable)" if col["nullable"] else ""
            col_descriptions.append(f"  - {col['name']}: {col['type']}{pk}{nullable}")

        doc = f"""Table: {table_name}
Row count: {row_count}
Columns:
{chr(10).join(col_descriptions)}

Sample data:
{json.dumps(table['sample_data'], indent=2)}"""

        documents.append({
            "id": f"table_{table_name}",
            "text": doc,
            "metadata": {"type": "table_schema", "table": table_name}
        })

    # 2. Relationship documents
    relationships = """
Database Relationships:
- orders.customer_id → customers.id (each order belongs to one customer)
- order_items.order_id → orders.id (each order can have multiple items)
- order_items.product_id → products.id (each item references a product)
- products.category_id → categories.id (each product belongs to one category)

Key Facts:
- order_date is stored as TEXT in 'YYYY-MM-DD' format
- Use strftime() for date operations in SQLite
- total_amount in orders is the sum of (unit_price * quantity) for all items
- discount in order_items is a decimal (0.1 = 10% off)
- customer segment can be 'Consumer', 'Corporate', or 'Small Business'
- order status can be 'completed', 'shipped', 'processing', or 'cancelled'
- region can be 'North', 'South', 'East', or 'West'
"""
    documents.append({
        "id": "relationships",
        "text": relationships,
        "metadata": {"type": "relationships", "table": "all"}
    })

    # 3. Example queries document
    example_queries = """
Example SQL Queries for this database:

1. Monthly revenue:
SELECT strftime('%Y-%m', order_date) as month, SUM(total_amount) as revenue
FROM orders WHERE status = 'completed' GROUP BY month ORDER BY month

2. Top products by revenue:
SELECT p.name, SUM(oi.unit_price * oi.quantity) as revenue
FROM order_items oi JOIN products p ON oi.product_id = p.id
JOIN orders o ON oi.order_id = o.id WHERE o.status = 'completed'
GROUP BY p.id ORDER BY revenue DESC LIMIT 10

3. Revenue by category:
SELECT c.name as category, SUM(oi.unit_price * oi.quantity) as revenue
FROM order_items oi JOIN products p ON oi.product_id = p.id
JOIN categories c ON p.category_id = c.id
JOIN orders o ON oi.order_id = o.id WHERE o.status = 'completed'
GROUP BY c.id ORDER BY revenue DESC

4. Customer segments analysis:
SELECT segment, COUNT(*) as customer_count, SUM(o.total_amount) as total_spent
FROM customers c JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'completed' GROUP BY segment

5. Orders by region:
SELECT region, COUNT(*) as order_count, SUM(total_amount) as revenue
FROM orders WHERE status = 'completed' GROUP BY region

6. Top customers by spend:
SELECT c.name, c.city, SUM(o.total_amount) as total_spent, COUNT(o.id) as order_count
FROM customers c JOIN orders o ON c.id = o.customer_id
WHERE o.status = 'completed' GROUP BY c.id ORDER BY total_spent DESC LIMIT 10

7. Daily order trends:
SELECT order_date, COUNT(*) as orders, SUM(total_amount) as revenue
FROM orders WHERE status = 'completed' GROUP BY order_date ORDER BY order_date

8. Average order value by month:
SELECT strftime('%Y-%m', order_date) as month, AVG(total_amount) as avg_order_value
FROM orders WHERE status = 'completed' GROUP BY month ORDER BY month

9. Product profit margins:
SELECT p.name, p.price, p.cost, ROUND((p.price - p.cost) / p.price * 100, 1) as margin_pct
FROM products p ORDER BY margin_pct DESC

10. Order status breakdown:
SELECT status, COUNT(*) as count, SUM(total_amount) as total
FROM orders GROUP BY status
"""
    documents.append({
        "id": "example_queries",
        "text": example_queries,
        "metadata": {"type": "example_queries", "table": "all"}
    })

    return documents


class SchemaRAG:
    """RAG system for database schema understanding."""

    def __init__(self):
        self.client = None
        self.collection = None
        self._initialized = False

    def initialize(self):
        """Initialize or load the RAG index."""
        if self._initialized:
            return

        try:
            self.client = chromadb.Client()
            # Try to get existing collection or create new
            try:
                self.collection = self.client.get_collection("schema_docs")
                self._initialized = True
                return
            except Exception:
                pass

            self.collection = self.client.create_collection(
                name="schema_docs",
                metadata={"hnsw:space": "cosine"}
            )

            documents = build_schema_documents()
            self.collection.add(
                ids=[doc["id"] for doc in documents],
                documents=[doc["text"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents]
            )
            self._initialized = True
            print(f"✅ Schema RAG initialized with {len(documents)} documents")

        except Exception as e:
            print(f"⚠️ RAG initialization error: {e}. Using fallback schema context.")
            self._initialized = True

    def query(self, question: str, n_results: int = 4) -> str:
        """Query the RAG index for relevant schema context."""
        self.initialize()

        if not self.collection:
            return self._fallback_context()

        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=min(n_results, self.collection.count())
            )

            if results and results["documents"]:
                return "\n\n---\n\n".join(results["documents"][0])
        except Exception as e:
            print(f"RAG query error: {e}")

        return self._fallback_context()

    def _fallback_context(self) -> str:
        """Fallback: return raw schema info if RAG fails."""
        try:
            schema_info = get_schema_info()
            parts = []
            for table in schema_info:
                cols = ", ".join([f"{c['name']} ({c['type']})" for c in table['columns']])
                parts.append(f"Table {table['table_name']}: {cols}")
            return "\n".join(parts)
        except Exception:
            return "Schema information unavailable."


# Global instance
schema_rag = SchemaRAG()
