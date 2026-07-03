import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .config import OPENROUTER_API_KEY
import sqlite3
import json


if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

def query_sales_database(sql_query: str) -> str:
    """
    Executes a standard SQL read query against the company sales database 
    and returns JSON-formatted results. Use this tool whenever a user asks 
    about revenue, categories, products, or units sold.
    
    Args:
        sql_query (str): The raw text SQL query string to run.
    """
    try:
        conn = sqlite3.connect("company_sales.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Formulate tabular format into structured JSON maps
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return json.dumps(results)
    except Exception as e:
        return f"Database Error: {str(e)}"

SYSTEM_PROMPT = """You are a Data Analyst Agent. Your job is to extract business insights.
You have access to a SQL database called 'sales' with the following schema:
- product_id (INTEGER)
- product_name (TEXT)
- category (TEXT)
- revenue (REAL)
- units_sold (INTEGER)

Always write and execute a valid SQL query via the provided tool before answering questions about metrics. 
"""

root_agent = Agent(
    name="Local_Data_Analyst",
    model=LiteLlm(
        model="openrouter/cohere/north-mini-code:free"
    ),
    instruction=f"{SYSTEM_PROMPT}\nAnalyze user data requests accurately and turn raw database returns into strategic insights.",
    tools=[query_sales_database]
)