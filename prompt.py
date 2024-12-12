import openai
import psycopg2
from psycopg2 import Error

# Define variables

# MODEL = "ft:gpt-4o-2024-08-06:personal:secmaster-2:AbFxfoSj"
MODEL= "ft:gpt-4o-2024-08-06:personal::Ad4WxL6P"
question = "find all high yield New York bonds, coupon between 3.0 and 5.0 inclusive, tax free"



from openai import OpenAI
import json

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=OPENAI_API_KEY,
)

def display_chat_history(messages):
    for message in messages:
        print(f"{message['role'].capitalize()}: {message['content']}")

def get_assistant_response(messages):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        max_tokens=150,
        temperature=0.0
    )
    response = r.choices[0].message.content
    return response

def get_table_schema(conn, table_name):
    schema_query = """
    SELECT
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_name = %s
    ORDER BY ordinal_position;
    """

    try:
        with conn.cursor() as cur:
            cur.execute(schema_query, (table_name,))
            columns = cur.fetchall()

            # Format columns as "col: type" strings
            col_descriptions = [f"{col[0]}: {col[1]}" for col in columns]
            schema_desc = ", ".join(col_descriptions)

            # Create the training data format
            training_data = {
                "messages": [
                    {"role": "system", "content": "You is a Postgres DB expert."},
                    {"role": "user", "content": f"table {table_name} schema"},
                    {"role": "assistant", "content": schema_desc}
                ]
            }

            # Write to file
            import json
            with open('schema.jsonl', 'a') as f:
                f.write(json.dumps(training_data) + '\n')

            print(f"\nSchema for {table_name} has been added to schema.jsonl")
            print(f"Schema for columns' name and type: {schema_desc}")

    except Error as e:
        print(f"Error getting schema for table {table_name}: {e}")
        return None

# messages = [{"role": "assistant", "content": "How can I help?"}]
messages = [{"role": "system", "content": "You are a Postgres DB expert."}]

# Add database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    # 'database': 'marketplace',
    'database': 'interface',
    'user': 'davidguo',
    'password': ''
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    print("Database connected successfully")
except Error as e:
    print(f"Error connecting to database: {e}")
    exit(1)

# get_table_schema(conn, 'entities')
# get_table_schema(conn, 'securities')
# get_table_schema(conn, 'marketdata')

iteration = 0
while True:
    iteration += 1
    print(f"\n\n--- Iteration {iteration} ---")

    user_input = input("User: ")
    messages.append({"role": "user", "content": user_input})
    display_chat_history(messages)

    print("\nGetting assistant response...")
    assistant_response = get_assistant_response(messages)
    messages.append({"role": "assistant", "content": assistant_response})

    # Execute the PostgreSQL query
    try:
        with conn.cursor() as cur:
            print(f"\nExecuting query: {assistant_response}")
            cur.execute(assistant_response)
            # Fetch and display results
            results = cur.fetchall()
            if results:
                print("\nQuery Results:")
                for row in results:
                    print(row)
            else:
                print("\nNo results found.")
            conn.commit()  # Commit after each query

    except Error as e:
        print(f"\nDatabase error: {e}")
        conn.rollback()  # Rollback on error
    except Exception as e:
        print(f"\nError: {e}")
        conn.rollback()  # Rollback on error

# Don't forget to close the connection when the program ends
conn.close()


"""
WITH best_bids_offers AS (
  SELECT
    isin,
    MAX(CASE WHEN kind = 'Bid' THEN price END) AS max_bid_price,
    MAX(CASE WHEN kind = 'Bid' THEN quantity END) AS max_bid_quantity,
    MAX(CASE WHEN kind = 'Bid' THEN yield END) AS max_bid_yield,
    MIN(CASE WHEN kind = 'Offer' THEN price END) AS min_offer_price,
    MIN(CASE WHEN kind = 'Offer' THEN quantity END) AS min_offer_quantity,
    MIN(CASE WHEN kind = 'Offer' THEN yield END) AS min_offer_yield
  FROM marketdata
  GROUP BY isin
)
SELECT
  s.isin,
  cusip,
  s.name,
  ticker,
  asset,
  grade,
  shortcut,
  benchmark,
  issue_date,
  maturity,
  income,
  coupon,
  frequency,
  issue_notional,
  outstanding,
  is_call,
  b.max_bid_quantity AS bid_quantity,
  b.max_bid_price AS bid_price,
  b.max_bid_yield AS bid_yield,
  b.min_offer_quantity AS ask_quantity,
  b.min_offer_price AS ask_price,
  b.min_offer_yield AS ask_yield
FROM securities s
JOIN entities e ON s.entity = e.entity
LEFT JOIN best_bids_offers b ON b.isin = s.isin;
"""