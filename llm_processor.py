import mysql.connector
import requests
import json
import re
import time
import sys

# Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3307, 
    'user': 'root',
    'password': 'root',
    'database': 'bid_data',
    'charset': 'utf8mb4'
}

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:14b" # User specified model

PROMPT_TEMPLATE = """
You are an expert data extractor. Your task is to extract key information from the following Government Procurement Announcement HTML content and output it as strictly valid JSON.

Extract the following fields:
- project_name: Project Name (项目名称)
- project_code: Project Code (项目编号)
- budget_amount: Budget Amount (预算金额/最高限价), as a number or string
- winning_bidder: Winning Bidder Name (中标供应商名称)
- winning_amount: Winning Amount (中标金额), as a number or string
- contact_person: Contact Person (联系人)
- contact_phone: Contact Phone (联系电话)

If a field is not found, use null.
Return ONLY the JSON object. Do not encompass it in markdown code blocks.

HTML Content:
{content}
"""

def clean_html(html_content):
    if not html_content:
        return ""
    # Remove script and style tags
    cleaned = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL)
    # Remove tags but keep some structure is hard, let's just use text extraction or raw html if small enough.
    # For LLM, raw HTML (stripped of scripts) is usually fine if context window allows.
    # Let's strip comments
    cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:10000] # Truncate to avoid context limit if too large

def get_unparsed_notices(cursor, limit=10):
    query = """
    SELECT n.id, n.content 
    FROM notices n 
    LEFT JOIN parsed_notices p ON n.id = p.notice_id 
    WHERE p.id IS NULL AND n.content IS NOT NULL
    LIMIT %s
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()

def call_ollama(content):
    prompt = PROMPT_TEMPLATE.format(content=content)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        # "format": "json" # DeepSeek R1 behaves better without forced JSON mode, allowing it to "think"
    }
    
    print(f"Calling Ollama for content length {len(content)}...")
    try:
        start_time = time.time()
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300) # Add timeout
        print(f"Ollama responded in {time.time() - start_time:.2f}s")
        response.raise_for_status()
        result = response.json()
        return result.get('response', '')
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        try:
             print(f"Ollama Response: {response.text}")
        except: pass
        return None
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def extract_json(text):
    # Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Try to find JSON block
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Fallback: try to find the first { and last }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
            
    return text

def save_result(conn, cursor, notice_id, raw_output):
    try:
        json_str = extract_json(raw_output)
        # Validate JSON
        parsed = json.loads(json_str)
        
        sql = """
        INSERT INTO parsed_notices (notice_id, parsed_json, raw_model_output)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (notice_id, json.dumps(parsed, ensure_ascii=False), raw_output))
        conn.commit()
        print(f"Saved parsed data for notice {notice_id}")
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for notice {notice_id}. Raw output length: {len(raw_output)}")
        # Save failed attempt
        try:
             sql = """
            INSERT INTO parsed_notices (notice_id, parsed_json, raw_model_output)
            VALUES (%s, %s, %s)
            """
             cursor.execute(sql, (notice_id, None, raw_output))
             conn.commit()
        except Exception as e:
             print(f"Failed to save error record: {e}")
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

def main():
    print("Starting LLM Processor...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        while True:
            notices = get_unparsed_notices(cursor)
            if not notices:
                print("No unparsed notices found. Sleeping...")
                time.sleep(10)
                continue
                
            for notice_id, content in notices:
                print(f"Processing notice {notice_id}...")
                cleaned_content = clean_html(content)
                
                llm_output = call_ollama(cleaned_content)
                if llm_output:
                    save_result(conn, cursor, notice_id, llm_output)
                else:
                    print(f"Skipping notice {notice_id} due to LLM failure.")
            
            # Optional: Add delay between batches
            
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
