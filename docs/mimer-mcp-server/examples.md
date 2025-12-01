The following section shows a few examples of how to use Mimer MCP Server through natural language queries in Copilot. The examples showcase how LLM-powered agents can autonomously discover and select appropriate MCP tools, handle errors and retries, and synthesize results into human-readable responses.

!!! tip "Tips on Guiding LLM Tool Selection"

    To improve tool selection accuracy, include explicit hints in your prompts such as `use Mimer MCP Server` or `use Mimer MCP tools`. This helps the LLM distinguish between generating SQL from scratch versus leveraging the available MCP tools. See [Tools](tools.md) for more tool-specific guidelines.

---

## Business Analytics in a Book Store

!!! info

    This example uses Mimer's example database which is based on a store that sells music and books, along with its e-commerce website. Learn more about [the Example Database](https://developer.mimer.com/article/the-example-database/).

### Top Spending Customers

This example shows the zero-shot capability of LLM-powered database agents with Claude Sonnet 4.5 as the reasoning model. Simply ask: `which customers have placed orders over 1000$`, the agent autonomously:

1. Lists available database schemas
2. Finds the right tables (customers, orders)
3. Checks column names and how tables relate to each other
4. Writes a SQL query with joins and aggregations
5. Executes the query and formats results for human consumption

<iframe allow="fullscreen;autoplay" allowfullscreen height="660" src="https://streamable.com/e/xj4fdr?autoplay=1&muted=1" width="632" style="border:none;"></iframe>

??? note "Expand to see the full interaction"

    ```
    User: Which customers have placed orders over 1000$?

    GitHub Copilot: I'll query the database to find customers who have placed orders over $1000. 

    Ran `list_schemas` 
    Completed with input: {}

    Ran `list_table_names` 
    Completed with input: {
    "schema": "mimer_store"
    }

    Ran `get_table_info` 
    Completed with input: {
    "schema": "mimer_store",
    "table_names": [
      "customers",
      "orders",
      "order_items"
    ],
    "sample_size": 3
    }

    Ran `execute_query` 
    Completed with input: {
    "query": "\nSELECT \n    c.customer_id,\n    c.forename,\n    c.surname,\n    c.email,\n    o.order_id,\n    o.order_no,\n    SUM(oi.VALUE) as order_total\nFROM mimer_store.customers c\nJOIN mimer_store.orders o ON c.customer_id = o.customer_id\nJOIN mimer_store.order_items oi ON o.order_id = oi.order_id\nGROUP BY c.customer_id, c.forename, c.surname, c.email, o.order_id, o.order_no\nHAVING SUM(oi.VALUE) > 1000\nORDER BY order_total DESC\n"
    }

    Ran `execute_query` 
    Completed with input: {
    "query": "\nSELECT \n    c.customer_id,\n    c.forename,\n    c.surname,\n    c.email,\n    o.order_id,\n    o.order_no,\n    SUM(oi.\"VALUE\") as order_total\nFROM mimer_store.customers c\nJOIN mimer_store.orders o ON c.customer_id = o.customer_id\nJOIN mimer_store.order_items oi ON o.order_id = oi.order_id\nGROUP BY c.customer_id, c.forename, c.surname, c.email, o.order_id, o.order_no\nHAVING SUM(oi.\"VALUE\") > 1000\nORDER BY order_total DESC\n"
    }

    Here are the customers who have placed orders over $1000:

    | Customer | Email | Order No | Order Total |
    |----------|-------|----------|-------------|
    | Sarah Williams | sarah.williams@email.com | ORD-2024-022 | $2,123.60 |
    | James Taylor | james.taylor@email.com | ORD-2024-027 | $1,789.67 |
    | Lisa Johnson | lisa.johnson@email.com | ORD-2024-008 | $1,681.56 |
    | Emma Davis | emma.davis@email.com | ORD-2024-017 | $1,563.58 |
    | Carlos Martinez | carlos.martinez@email.com | ORD-2024-004 | $1,457.43 |
    | Michael Brown | michael.brown@email.com | ORD-2024-013 | $1,229.72 |
    | Sarah Williams | sarah.williams@email.com | ORD-2024-002 | $1,218.67 |
    | Emma Davis | emma.davis@email.com | ORD-2024-006 | $1,096.66 |

    In total, **6 unique customers** have placed orders over $1000, with Sarah Williams and Emma Davis each having 2 orders above this threshold.

    ```

---

### Best-selling Products

This demo shows how to find best-selling products and follow up with questions about customer demographics. The agent showcases key LLM capabilities:

- **Autonomous Discovery**: The agent automatically calls `list_schemas` and `get_table_info` to understand the database structure
- **Self-Correction**: When it hits a syntax error, it reads the error message and fixes the SQL on its own
- **Context Retention**:  Once the agent understands the schema, users can continue the conversation with follow-up questions about customer demographics, contact information for CRM, or other business metrics

<iframe allow="fullscreen;autoplay" allowfullscreen height="660" src="https://streamable.com/e/g1qyym?autoplay=1&muted=1" width="632" style="border:none;"></iframe>

??? note "Expand to see the full interaction"

    ```
    User: What are our top selling products?

    GitHub Copilot: I'll query the database to find the top selling products. 

    Ran `list_schemas` 
    Completed with input: {}

    Ran `list_table_names` 
    Completed with input: {
      "schema": "mimer_store"
    }

    Ran `get_table_info` 
    Completed with input: {
      "schema": "mimer_store",
      "table_names": [
        "products",
        "order_items",
        "orders"
      ],
      "sample_size": 3
    }

    Ran `get_table_info` 
    Completed with input: {
      "sample_size": 3,
      "schema": "mimer_store",
      "table_names": [
        "items"
      ]
    }

    Ran `execute_query` 
    Completed with input: {
      "query": "\nSELECT \n    p.product,\n    SUM(oi.quantity) as total_quantity_sold,\n    SUM(oi.VALUE) as total_revenue,\n    COUNT(DISTINCT oi.order_id) as number_of_orders\nFROM mimer_store.order_items oi\nJOIN mimer_store.items i ON oi.item_id = i.item_id\nJOIN mimer_store.products p ON i.product_id = p.product_id\nGROUP BY p.product\nORDER BY total_quantity_sold DESC\nLIMIT 10\n"
    }

    Ran `execute_query` 
    Completed with input: {
      "query": "\nSELECT \n    p.product,\n    SUM(oi.quantity) as total_quantity_sold,\n    SUM(oi.\"VALUE\") as total_revenue,\n    COUNT(DISTINCT oi.order_id) as number_of_orders\nFROM mimer_store.order_items oi\nJOIN mimer_store.items i ON oi.item_id = i.item_id\nJOIN mimer_store.products p ON i.product_id = p.product_id\nGROUP BY p.product\nORDER BY total_quantity_sold DESC\nFETCH FIRST 10 ROWS ONLY\n"
    }

    Here are the top 10 selling products:

    | Product | Total Quantity Sold | Total Revenue | Number of Orders |
    |---------|-------------------|---------------|------------------|
    | A Prairie Legend | 73 | $8,466.54 | 13 |
    | Harry Potter and the Prisoner of Azkaban | 60 | $2,435.40 | 6 |
    | Harry Potter and the Chamber of Secrets | 45 | $1,749.55 | 5 |
    | Harry Potter and the Philosopher's Stone | 38 | $898.62 | 6 |
    | 71 Minutes of Faust | 13 | $259.74 | 2 |
    | Amazing Grace: His Greatest Sacred Songs | 13 | $389.74 | 5 |
    | A Day in the Life of a Clarinet | 11 | $219.78 | 3 |
    | A Centenary Celebration | 10 | $509.80 | 3 |
    | 20 Vodka Jellies | 7 | $118.86 | 1 |
    | 1944 | 6 | $113.88 | 2 |

    **A Prairie Legend** is the clear winner with 73 units sold across 13 orders, generating over $8,400 in revenue. The Harry Potter series also performs very well with three titles in the top 4.

    User: From which country are our customers who bought Harry Potter from?

    GitHub Copilot: I'll find out which countries our Harry Potter customers are from. 

    Ran `get_table_info` 
    Completed with input: {
      "sample_size": 3,
      "schema": "mimer_store",
      "table_names": [
        "customers",
        "countries"
      ]
    }

    Ran `execute_query` 
    Completed with input: {
      "query": "\nSELECT \n    c.country,\n    COUNT(DISTINCT cu.customer_id) as customer_count,\n    SUM(oi.quantity) as total_harry_potter_books,\n    SUM(oi.\"VALUE\") as total_spent\nFROM mimer_store.order_items oi\nJOIN mimer_store.orders o ON oi.order_id = o.order_id\nJOIN mimer_store.customers cu ON o.customer_id = cu.customer_id\nJOIN mimer_store.countries c ON cu.country_code = c.code\nJOIN mimer_store.items i ON oi.item_id = i.item_id\nJOIN mimer_store.products p ON i.product_id = p.product_id\nWHERE p.product LIKE '%Harry Potter%'\nGROUP BY c.country\nORDER BY customer_count DESC, total_harry_potter_books DESC\n"
    }

    Our Harry Potter customers are from 4 countries:

    | Country | Customers | Books Purchased | Total Spent |
    |---------|-----------|-----------------|-------------|
    | United States | 4 | 66 | $2,030.34 |
    | Canada | 2 | 33 | $1,522.67 |
    | Germany | 2 | 28 | $1,168.72 |
    | Australia | 2 | 16 | $361.84 |

    The **United States** leads with 4 customers who purchased 66 Harry Potter books, followed by Canada, Germany, and Australia with 2 customers each.

    User: What are their emails?

    GitHub Copilot: Ran `execute_query` 
    Completed with input: {
      "query": "\nSELECT \n    cu.forename,\n    cu.surname,\n    cu.email,\n    c.country,\n    SUM(oi.quantity) as harry_potter_books_purchased,\n    SUM(oi.\"VALUE\") as total_spent\nFROM mimer_store.order_items oi\nJOIN mimer_store.orders o ON oi.order_id = o.order_id\nJOIN mimer_store.customers cu ON o.customer_id = cu.customer_id\nJOIN mimer_store.countries c ON cu.country_code = c.code\nJOIN mimer_store.items i ON oi.item_id = i.item_id\nJOIN mimer_store.products p ON i.product_id = p.product_id\nWHERE p.product LIKE '%Harry Potter%'\nGROUP BY cu.forename, cu.surname, cu.email, c.country\nORDER BY c.country, total_spent DESC\n"
    }

    Here are the customers who purchased Harry Potter books:

    **Australia:**
    - jessica.moore@email.com (Jessica Moore) - 14 books, $339.86
    - michael.brown@email.com (Michael Brown) - 2 books, $21.98

    **Canada:**
    - lisa.johnson@email.com (Lisa Johnson) - 30 books, $1,489.70
    - jennifer.chen@email.com (Jennifer Chen) - 3 books, $32.97

    **Germany:**
    - carlos.martinez@email.com (Carlos Martinez) - 23 books, $1,138.77
    - robert.wilson@email.com (Robert Wilson) - 5 books, $29.95

    **United States:**
    - sarah.williams@email.com (Sarah Williams) - 23 books, $963.77
    - emma.davis@email.com (Emma Davis) - 22 books, $895.78
    - james.taylor@email.com (James Taylor) - 20 books, $159.80
    - thomas.anderson@email.com (Thomas Anderson) - 1 book, $10.99

    ```

---

## Using Stored Procedure Tools

Stored procedures often have domain-specific logic (e.g., fuzzy matching algorithms, business rules) which can be challenging for an LLM to recreate correctly. By pointing the agent to existing procedures, we can use the database logic instead of hoping the LLM gets it right on its own.

!!! tip "Prompt Engineering for Stored Procedures"

    **Be explicit**: Without guidance, LLMs will write SQL from scratch. Add phrases like "use stored procedure" or "call existing procedures" to your prompt, and the agent changes from code generation to tool discovery mode.

**User prompt:** `Use stored procedures to find books that sound like 'harie pottar'`

<div style="position:relative; width:100%; height:0px; padding-bottom:104.430%"><iframe allow="fullscreen;autoplay" allowfullscreen height="100%" src="https://streamable.com/e/utbv5u?autoplay=1&muted=1" width="100%" style="border:none; width:100%; height:100%; position:absolute; left:0px; top:0px; overflow:hidden;"></iframe></div>

??? note "Expand to see the full interaction"

    ```
    User: use stored procedures to find books that sound like 'harie pottar'

    GitHub Copilot: Created 6 todos

    I’ll scan schemas and tables to find books and relevant procedures.

    Ran `list_schemas` 
    Completed with input: {}

    Starting: *Find books table* (2/6)

    Ran `list_table_names` 
    Completed with input: {
      "schema": "mimer_store_book"
    }

    Ran `list_table_names` 
    Completed with input: {
      "schema": "mimer_store"
    }

    Ran `list_table_names` 
    Completed with input: {
      "schema": "mimer_store_music"
    }

    Ran `list_table_names` 
    Completed with input: {
      "schema": "mimer_store_web"
    }

    Starting: *Locate matching procedures* (3/6)

    Ran `list_stored_procedures` 
    Completed with input: {}

    Ran `get_stored_procedure_parameters` 
    Completed with input: {
      "procedure_schema": "mimer_store_book",
      "procedure_name": "search"
    }

    Ran `get_stored_procedure_definition` 
    Completed with input: {
      "procedure_schema": "mimer_store_book",
      "procedure_name": "search"
    }

    Ran `execute_stored_procedure` 
    Completed with input: {
      "procedure_schema": "mimer_store_book",
      "procedure_name": "search",
      "parameters": "{\"p_book_title\":\"harie pottar\",\"p_author\":\"\"}"
    }

    Completed: *Locate matching procedures* (3/6)

    Plan: find a suitable stored procedure for fuzzy book search and run it with your input.

    - Action: Used `mimer_store_book.search` stored procedure with `p_book_title='harie pottar'` and empty `p_author` to allow any author match.
    - Result: Retrieved likely matches that “sound like” your input.

    Results
    - Title: Harry Potter and the Chamber of Secrets — Author: Rowling, J.K. — Format: Hardcover — Price: 10.99 — Item ID: 60769
    - Title: Harry Potter and the Chamber of Secrets — Author: Rowling, J.K. — Format: Paperback — Price: 5.99 — Item ID: 60770
    - Title: Harry Potter and the Chamber of Secrets — Author: Rowling, J.K.; Fry, Stephen — Format: Audio CD — Price: 42.99 — Item ID: 60771
    - Title: Harry Potter and the Philosopher's Stone — Author: Rowling, J.K. — Format: Hardcover — Price: 10.99 — Item ID: 60772
    - Title: Harry Potter and the Philosopher's Stone — Author: Rowling, J.K. — Format: Paperback — Price: 5.99 — Item ID: 60773
    - Title: Harry Potter and the Philosopher's Stone — Author: Rowling, J.K.; Fry, Stephen — Format: Audio CD — Price: 37.99 — Item ID: 60775
    - Title: Harry Potter and the Philosopher's Stone — Author: Rowling, J.K.; Fry, Stephen — Format: Audio Cassette — Price: 21.99 — Item ID: 60774
    - Title: Harry Potter and the Prisoner of Azkaban — Author: Rowling, J.K. — Format: Hardcover — Price: 10.99 — Item ID: 60776
    - Title: Harry Potter and the Prisoner of Azkaban — Author: Rowling, J.K. — Format: Paperback — Price: 5.99 — Item ID: 60777
    - Title: Harry Potter and the Prisoner of Azkaban — Author: Rowling, J.K.; Fry, Stephen — Format: Audio CD — Price: 52.99 — Item ID: 60778

    Notes
    - Procedure: `mimer_store_book.search(p_book_title VARCHAR(48), p_author VARCHAR(48))` returns a result set of `title, authors_list, format, price, item_id`.
    - It leverages `mimer_store.product_search_code(...)`, which provides the fuzzy/phonetic match effect for misspellings like “harie pottar”.

    Want me to refine further (e.g., restrict to a specific format or author), or export these results to CSV/JSON?

    ```

