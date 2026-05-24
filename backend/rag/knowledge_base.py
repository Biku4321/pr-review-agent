"""
RAG knowledge base seeded with OWASP Top 10 + common CVE patterns.
Uses in-memory vector store (no external DB needed) for hackathon simplicity.
Falls back gracefully if chromadb not installed.
"""

OWASP_KNOWLEDGE = [
    # A01 - Broken Access Control
    {
        "id": "OWASP-A01-001",
        "title": "Broken Access Control - Missing Authorization Check",
        "category": "security",
        "severity": "critical",
        "description": "Functions that modify data or access sensitive resources must verify the caller has permission. Missing @login_required, @permission_required, or manual auth checks before database writes/reads.",
        "patterns": ["def delete_", "def update_", "def admin_", "request.user", "is_authenticated", "has_permission"],
        "example_bad": "def delete_user(user_id): db.delete(user_id)  # No auth check",
        "example_good": "def delete_user(request, user_id):\n    if not request.user.is_admin: raise PermissionError\n    db.delete(user_id)",
        "cwe": "CWE-284",
        "references": ["https://owasp.org/Top10/A01_2021-Broken_Access_Control/"],
    },
    # A02 - Cryptographic Failures
    {
        "id": "OWASP-A02-001",
        "title": "Weak Password Hashing - MD5/SHA1",
        "category": "security",
        "severity": "critical",
        "description": "MD5 and SHA1 are cryptographically broken and must never be used for password hashing. Use bcrypt, argon2, or PBKDF2 with a salt.",
        "patterns": ["md5", "sha1", "hashlib.md5", "hashlib.sha1"],
        "example_bad": "hashlib.md5(password.encode()).hexdigest()",
        "example_good": "import bcrypt\nbcrypt.hashpw(password.encode(), bcrypt.gensalt())",
        "cwe": "CWE-327",
        "references": ["https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"],
    },
    {
        "id": "OWASP-A02-002",
        "title": "Hardcoded Cryptographic Key or Secret",
        "category": "security",
        "severity": "critical",
        "description": "API keys, JWT secrets, database passwords and other credentials must never be hardcoded in source code. Use environment variables or a secrets manager.",
        "patterns": ["SECRET_KEY =", "API_KEY =", "PASSWORD =", "TOKEN =", "secret ="],
        "example_bad": 'SECRET_KEY = "mysecretkey123"',
        "example_good": 'SECRET_KEY = os.environ["SECRET_KEY"]',
        "cwe": "CWE-798",
        "references": ["https://cwe.mitre.org/data/definitions/798.html"],
    },
    # A03 - Injection
    {
        "id": "OWASP-A03-001",
        "title": "SQL Injection via String Concatenation",
        "category": "security",
        "severity": "critical",
        "description": "User input interpolated directly into SQL queries allows attackers to manipulate query logic, exfiltrate data, or drop tables. Always use parameterized queries or an ORM.",
        "patterns": ["f\"SELECT", "f'SELECT", "% username", "+ user_input", "format(", "% ("],
        "example_bad": 'query = f"SELECT * FROM users WHERE name = \'{username}\'"',
        "example_good": 'cursor.execute("SELECT * FROM users WHERE name = %s", (username,))',
        "cwe": "CWE-89",
        "cvss": 9.8,
        "references": ["https://owasp.org/Top10/A03_2021-Injection/"],
    },
    {
        "id": "OWASP-A03-002",
        "title": "Command Injection via subprocess/os.system",
        "category": "security",
        "severity": "critical",
        "description": "Passing user input to shell commands without sanitization allows arbitrary OS command execution.",
        "patterns": ["os.system(", "subprocess.call(", "subprocess.run(", "shell=True"],
        "example_bad": 'os.system(f"ping {user_input}")',
        "example_good": 'subprocess.run(["ping", user_input], shell=False)',
        "cwe": "CWE-78",
        "cvss": 9.8,
    },
    {
        "id": "OWASP-A03-003",
        "title": "NoSQL Injection",
        "category": "security",
        "severity": "high",
        "description": "MongoDB and other NoSQL databases are vulnerable to operator injection when user input is used directly in queries without sanitization.",
        "patterns": ["find({", "find_one({", "$where", "$regex"],
        "example_bad": 'db.users.find({"username": username, "password": password})',
        "example_good": "# Validate input types strictly; use ODM like mongoengine",
        "cwe": "CWE-943",
    },
    # A04 - Insecure Design
    {
        "id": "OWASP-A04-001",
        "title": "Missing Rate Limiting on Authentication Endpoints",
        "category": "security",
        "severity": "high",
        "description": "Login, password reset, and registration endpoints without rate limiting are vulnerable to brute force and credential stuffing attacks.",
        "patterns": ["def login(", "def authenticate(", "/login", "/auth", "check_password"],
        "example_bad": "@app.route('/login', methods=['POST'])\ndef login(): ...",
        "example_good": "@app.route('/login')\n@limiter.limit('5/minute')\ndef login(): ...",
        "cwe": "CWE-307",
    },
    # A05 - Security Misconfiguration
    {
        "id": "OWASP-A05-001",
        "title": "Debug Mode Enabled in Production",
        "category": "security",
        "severity": "high",
        "description": "Debug mode exposes stack traces, environment variables, and interactive consoles to attackers.",
        "patterns": ["DEBUG = True", "debug=True", "app.run(debug=True)"],
        "example_bad": "app.run(debug=True)",
        "example_good": 'app.run(debug=os.environ.get("DEBUG", "false").lower() == "true")',
        "cwe": "CWE-94",
    },
    # A07 - Identification and Authentication Failures
    {
        "id": "OWASP-A07-001",
        "title": "JWT Without Signature Verification",
        "category": "security",
        "severity": "critical",
        "description": "Decoding a JWT without verifying its signature allows attackers to forge tokens and impersonate any user.",
        "patterns": ["jwt.decode(", "verify=False", "options={\"verify_signature\": False}"],
        "example_bad": 'jwt.decode(token, options={"verify_signature": False})',
        "example_good": 'jwt.decode(token, SECRET_KEY, algorithms=["HS256"])',
        "cwe": "CWE-347",
        "cvss": 9.1,
    },
    # A08 - Software and Data Integrity Failures
    {
        "id": "OWASP-A08-001",
        "title": "Insecure Deserialization with pickle",
        "category": "security",
        "severity": "critical",
        "description": "Python pickle can execute arbitrary code during deserialization. Never unpickle data from untrusted sources.",
        "patterns": ["pickle.loads(", "pickle.load(", "cPickle"],
        "example_bad": "data = pickle.loads(user_data)",
        "example_good": "data = json.loads(user_data)  # Use JSON for untrusted data",
        "cwe": "CWE-502",
        "cvss": 9.8,
    },
    # A09 - Security Logging and Monitoring Failures
    {
        "id": "OWASP-A09-001",
        "title": "Sensitive Data in Logs",
        "category": "security",
        "severity": "medium",
        "description": "Logging passwords, tokens, credit card numbers, or PII creates a compliance violation and security risk.",
        "patterns": ["logger.info(password", "print(password", "log.debug(token", "logging.info(user"],
        "example_bad": 'logger.info(f"User {username} logged in with password {password}")',
        "example_good": 'logger.info(f"User {username} logged in successfully")',
        "cwe": "CWE-532",
    },
    # A10 - SSRF
    {
        "id": "OWASP-A10-001",
        "title": "Server-Side Request Forgery (SSRF)",
        "category": "security",
        "severity": "high",
        "description": "Making HTTP requests to user-supplied URLs without validation allows attackers to reach internal services, cloud metadata endpoints (169.254.169.254), or perform port scanning.",
        "patterns": ["requests.get(url", "httpx.get(url", "urllib.request.urlopen(url"],
        "example_bad": "response = requests.get(user_supplied_url)",
        "example_good": "# Validate URL against allowlist of domains before fetching",
        "cwe": "CWE-918",
        "cvss": 8.6,
    },
    # Path Traversal
    {
        "id": "CWE-022-001",
        "title": "Path Traversal - Directory Traversal Attack",
        "category": "security",
        "severity": "high",
        "description": "Constructing file paths from user input without normalization and validation allows attackers to read arbitrary files (../../etc/passwd).",
        "patterns": ["open(", "os.path.join(", "base_dir +", "file_path ="],
        "example_bad": 'open(base_dir + filename)',
        "example_good": "safe = os.path.realpath(os.path.join(base_dir, filename))\nif not safe.startswith(base_dir): raise ValueError",
        "cwe": "CWE-22",
        "cvss": 7.5,
    },
    # XSS
    {
        "id": "OWASP-A03-XSS-001",
        "title": "Cross-Site Scripting (XSS) - Reflected",
        "category": "security",
        "severity": "high",
        "description": "Inserting user input directly into HTML without escaping allows attackers to inject malicious scripts that run in victims' browsers.",
        "patterns": ["innerHTML", "f\"<", "f'<", "Markup(", ".format("],
        "example_bad": 'return f"<p>Hello {name}</p>"',
        "example_good": "from markupsafe import escape\nreturn f'<p>Hello {escape(name)}</p>'",
        "cwe": "CWE-79",
        "cvss": 6.1,
    },
    # Performance patterns
    {
        "id": "PERF-001",
        "title": "N+1 Query Problem",
        "category": "performance",
        "severity": "high",
        "description": "Executing a database query inside a loop results in N+1 queries (1 to get the list + N to get details). This is the most common Django/SQLAlchemy performance killer.",
        "patterns": ["for ", "query.filter", "objects.get", "session.query"],
        "example_bad": "for user in users:\n    orders = Order.objects.filter(user=user)",
        "example_good": "users = User.objects.prefetch_related('orders').all()",
        "cwe": None,
    },
]


def get_relevant_context(code_snippet: str, category: str = "security", top_k: int = 5) -> str:
    """
    Simple keyword-based retrieval of relevant OWASP/CVE context.
    In production, replace with vector similarity search (chromadb/pgvector).
    """
    scored = []
    code_lower = code_snippet.lower()

    for entry in OWASP_KNOWLEDGE:
        if entry.get("category") != category and category != "all":
            continue
        score = 0
        for pattern in entry.get("patterns", []):
            if pattern.lower() in code_lower:
                score += 3
        # Title/description keyword matching
        for word in entry["title"].lower().split():
            if len(word) > 4 and word in code_lower:
                score += 1
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return ""

    lines = ["## Relevant Security Knowledge Base Entries\n"]
    for _, entry in top:
        lines.append(f"### [{entry['id']}] {entry['title']}")
        lines.append(f"**Severity:** {entry['severity'].upper()} | **CWE:** {entry.get('cwe', 'N/A')}")
        if entry.get("cvss"):
            lines.append(f"**CVSS:** {entry['cvss']}/10")
        lines.append(f"**Description:** {entry['description']}")
        lines.append(f"**Vulnerable pattern:** `{entry['example_bad']}`")
        lines.append(f"**Secure alternative:** `{entry['example_good']}`")
        if entry.get("references"):
            lines.append(f"**Reference:** {entry['references'][0]}")
        lines.append("")

    return "\n".join(lines)
