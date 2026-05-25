"""
Run a local review test without needing a real GitHub repo.
Usage: cd backend && python test_local.py
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(".env")
from agents.orchestrator import run_review
SAMPLE_FILES = [
    {
        "filename": "app/users.py",
        "status": "modified",
        "additions": 30,
        "deletions": 2,
        "patch": """\
+import sqlite3
+
+DB_PASSWORD = "super_secret_password_123"
+SECRET_KEY = "hardcoded_jwt_secret_abc"
+
+def get_user(username, password):
+    conn = sqlite3.connect('users.db')
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    cursor = conn.execute(query)
+    return cursor.fetchone()
+
+def render_profile(user_input):
+    html = f"<div>Welcome, {user_input['name']}!</div>"
+    return html
+
+def get_all_orders(user_id):
+    conn = sqlite3.connect('orders.db')
+    orders = conn.execute("SELECT * FROM orders WHERE user_id = ?", [user_id]).fetchall()
+    for order in orders:
+        items = conn.execute(f"SELECT * FROM items WHERE order_id = {order['id']}").fetchall()
+    return orders
+
+def hash_password(pwd):
+    import hashlib
+    return hashlib.md5(pwd.encode()).hexdigest()
""",
    }
]

SAMPLE_METADATA = {
    "title": "Add user authentication and order fetching",
    "body": "Implements user login and order retrieval",
    "author": "developer",
    "base_branch": "main",
    "head_branch": "feature/auth",
    "url": "https://github.com/demo/repo/pull/1",
    "additions": 30,
    "deletions": 2,
    "changed_files": 1,
}


async def main():
    print("🚀 Running multi-agent review...\n")
    state = await run_review("demo/repo", 1, SAMPLE_FILES, SAMPLE_METADATA)

    print(f"✅ Review complete in {state['total_time_ms']}ms\n")
    print(f"📝 Summary: {state['overall_summary']}\n")

    for key in ["security_result", "performance_result", "quality_result"]:
        result = state.get(key)
        if result:
            print(f"--- {result.agent_name} ({result.execution_time_ms}ms) ---")
            print(f"Summary: {result.summary}")
            for issue in result.issues:
                print(f"  [{issue.severity.upper()}] {issue.title} ({issue.file_path})")
            print()

    total = len(state["all_issues"])
    critical = sum(1 for i in state["all_issues"] if i.severity.value == "critical")
    print(f"Total: {total} issues, {critical} critical")


if __name__ == "__main__":
    asyncio.run(main())
