from lexer import tokenize

TEST_CASES = [
    (
        "Basic SELECT with WHERE",
        "SELECT * FROM employees WHERE dept_id = 10;"
    ),
    (
        "Arithmetic expression + FLOAT literal",
        "SELECT name, salary * 1.1 AS new_sal FROM staff WHERE salary >= 50000.0;"
    ),
    (
        "JOIN with table alias and DOT notation",
        "SELECT e.name FROM employees e JOIN departments d ON e.dept_id = d.id"
    ),
    (
        "Multi-line query with line comment and NEQ operator",
        "-- get all active users\nSELECT id, email FROM users WHERE active <> 0 LIMIT 25;"
    ),
    (
        "String literal with escaped apostrophe",
        "SELECT * FROM users WHERE name = 'O\\'Brien';"
    ),
    (
        "Subexpression with parentheses",
        "SELECT (salary + bonus) * 1.2 FROM employees;"
    ),
]


def main():
    sep = "=" * 60
    for title, query in TEST_CASES:
        print(sep)
        print(f"TEST: {title}")
        print(f"INPUT: {query!r}")
        print(sep)
        tokens = tokenize(query)
        for tok in tokens:
            print(f"  {tok}")
        print()


if __name__ == "__main__":
    main()
