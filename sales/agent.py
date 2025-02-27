import sqlite3
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from sales_agent.settings import BASE_DIR

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

def execute_sql(query):
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query.strip())
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return result
    except sqlite3.Error as e:
        return f"Database error: {e}"

sql_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful sales assistant. Given a user question, generate the appropriate SQL query to retrieve the answer from an SQLite database.
    The database has the following tables:
    - sales_product (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, stock INTEGER)
    - sales_sale (id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, sale_date DATETIME)
    - sales_customer (id INTEGER PRIMARY KEY, name TEXT, email TEXT)
    - sales_customersale (id INTEGER PRIMARY KEY, customer_id INTEGER, sale_id INTEGER)
    Only return the SQL query. Do not provide any additional explanation or markdown code blocks. If the question cannot be answered with the current database schema, return an error message."""),
    ("human", "{question}")
])

sql_chain = (
    {"question": RunnableLambda(lambda x: x)}
    | sql_prompt
    | model
    | StrOutputParser()
    | RunnableLambda(execute_sql)
)

response_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful sales assistant. Format the results of the SQL query into a natural language response for the user.
    If the result contains product information, include the product name and price.
    If the result contains customer information, include the customer name.
    If the result contains sale information, include the product name, quantity, and sale date.
    If there are multiple rows, format them in a readable list.
    If there are no results, tell the user that no results were found.
    If there is an error, tell the user that there was an error with the database."""),
    ("human", "Question: {question}\nSQL Result: {sql_result}")
])

response_chain = (
    {"question": RunnableLambda(lambda x: x["question"]), "sql_result": RunnableLambda(lambda x: x["sql_result"])}
    | response_prompt
    | model
    | StrOutputParser()
)

def sales_agent(question):
    sql_result = sql_chain.invoke(question)

    if "error" in str(sql_result).lower():
        return "I encountered an error while accessing the database. Please try again later."
    elif not sql_result:
        return "I couldn't find any information related to your query."

    response = response_chain.invoke({"question": question, "sql_result": sql_result})
    return response