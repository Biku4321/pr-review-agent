# Sample Demo PR - Vulnerable Code
# This file simulates a PR diff with intentional security vulnerabilities
# Use this to test the agent locally without a real GitHub repo

DEMO_DIFF = """
diff --git a/app/users.py b/app/users.py
index abc123..def456 100644
--- a/app/users.py
+++ b/app/users.py
@@ -1,20 +1,45 @@
+import sqlite3
+import os
+
+# Hardcoded credentials - DO NOT COMMIT
+DB_PASSWORD = "super_secret_password_123"
+SECRET_KEY = "hardcoded_jwt_secret"
+
+def get_user(username, password):
+    # SQL Injection vulnerability
+    conn = sqlite3.connect('users.db')
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    cursor = conn.execute(query)
+    return cursor.fetchone()
+
+def render_profile(user_input):
+    # XSS vulnerability - unescaped user content
+    html = f"<div>Welcome, {user_input['name']}!</div>"
+    return html
+
+def get_all_orders(user_id):
+    conn = sqlite3.connect('orders.db')
+    # N+1 query problem
+    orders = conn.execute("SELECT * FROM orders WHERE user_id = ?", [user_id]).fetchall()
+    for order in orders:
+        # This fires a DB query for EVERY order
+        items = conn.execute(f"SELECT * FROM items WHERE order_id = {order['id']}").fetchall()
+    return orders
+
+def process_file(filename):
+    # Path traversal vulnerability
+    base_dir = "/uploads/"
+    file_path = base_dir + filename  # user can pass ../../etc/passwd
+    with open(file_path, 'r') as f:
+        return f.read()
+
+def hash_password(pwd):
+    import md5  # Weak hashing algorithm
+    return md5.new(pwd).hexdigest()
"""
