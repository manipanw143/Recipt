import re
import json
import logging
import time
import requests
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Configure retry strategy for Ollama API
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

@app.errorhandler(400)
def handle_bad_request(e):
    logger.error(f"Bad request: {str(e)}")
    return jsonify({
        "error": "Invalid request format",
        "details": "Please check your request payload",
        "reference_id": str(uuid.uuid4())
    }), 400

@app.errorhandler(500)
def handle_server_error(e):
    logger.exception("Server error occurred")
    return jsonify({
        "error": "Internal server error",
        "resolution": "Please try again with a simpler request",
        "reference_id": str(uuid.uuid4())
    }), 500

def fetch_swagger_spec(url):
    try:
        logger.info(f"Fetching Swagger spec from: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching Swagger spec: {str(e)}")
        raise

def chunk_endpoints(swagger_spec, chunk_size=2):
    """Group endpoints into smaller, more manageable chunks"""
    endpoints = []
    for path, methods in swagger_spec.get('paths', {}).items():
        for method in ['get', 'post', 'put', 'delete', 'patch']:
            if method in methods:
                endpoint_info = {
                    "path": path,
                    "method": method.upper(),
                    "operation": methods[method]
                }
                endpoints.append(endpoint_info)
    
    # Use smaller chunks for better JSON generation
    return [endpoints[i:i + chunk_size] 
            for i in range(0, len(endpoints), chunk_size)]

def build_chunked_prompt(chunk, additional_prompt):
    """Create a focused prompt for a chunk of endpoints with strict JSON rules"""
    endpoint_list = "\n".join([f"- {e['method']} {e['path']}" for e in chunk])
    
    return f"""You are a healthcare API test generator. Generate ONLY valid JSON in the exact format shown below.

CRITICAL RULES:
1. Output ONLY JSON - no explanations, no markdown, no extra text
2. Use exactly this structure with proper commas and quotes
3. Each endpoint must have exactly 3 test cases
4. All strings must use double quotes
5. No trailing commas

REQUIRED JSON FORMAT:
{{
  "test_suite": [
    {{
      "endpoint": "/exact/path",
      "method": "GET",
      "test_cases": [
        {{
          "name": "Valid request with authentication",
          "type": "positive",
          "headers": {{"Authorization": "Bearer valid_token"}},
          "expected_status": 200
        }},
        {{
          "name": "Missing authentication token",
          "type": "authentication", 
          "headers": {{}},
          "expected_status": 401
        }},
        {{
          "name": "Invalid input data",
          "type": "negative",
          "body": {{"invalid": "data"}},
          "expected_status": 400
        }}
      ]
    }}
  ]
}}

Generate test cases for these endpoints:
{endpoint_list}

Additional requirements: {additional_prompt}

Remember: Output ONLY the JSON structure above with no other text."""

def advanced_json_repair(json_str):
    """Enhanced JSON repair with multiple strategies"""
    if not json_str or not json_str.strip():
        return {"test_suite": []}
    
    # Clean the input
    json_str = json_str.strip()
    
    # Strategy 1: Extract JSON from markdown or extra text
    json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(0).strip()
    
    # Strategy 2: Fix common JSON issues
    repairs = [
        # Fix missing commas between objects
        (r'}\s*{', '},{'),
        # Fix missing commas between array elements
        (r']\s*\[', '],['),
        # Fix missing commas after values before next key
        (r'(["\d\]}\s])\s*("[\w])', r'\1,\2'),
        # Fix unquoted keys (word followed by colon)
        (r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3'),
        # Remove trailing commas
        (r',\s*([}\]])', r'\1'),
        # Fix endpoint path issues - remove leading commas
        (r'"endpoint"\s*:\s*,\s*"([^"]+)"', r'"endpoint": "\1"'),
        # Fix method issues - remove leading commas  
        (r'"method"\s*:\s*,\s*"([^"]+)"', r'"method": "\1"'),
        # Fix double commas
        (r',,+', ','),
        # Fix space issues around colons
        (r'"\s*:\s*([^,}\]]+)([,}\]])', r'": \1\2'),
    ]
    
    for pattern, replacement in repairs:
        json_str = re.sub(pattern, replacement, json_str)
    
    # Strategy 3: Try to parse, if fails, create minimal valid structure
    try:
        parsed = json.loads(json_str)
        # Validate structure
        if not isinstance(parsed, dict) or "test_suite" not in parsed:
            raise ValueError("Invalid structure")
        if not isinstance(parsed["test_suite"], list):
            raise ValueError("test_suite must be array")
        return parsed
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"JSON repair failed: {e}")
        logger.warning(f"Problematic JSON: {json_str[:200]}...")
        
        # Strategy 4: Try to extract valid parts
        try:
            # Look for individual endpoint objects
            endpoint_pattern = r'\{\s*"endpoint"\s*:\s*"[^"]+"\s*,\s*"method"\s*:\s*"[^"]+"\s*,\s*"test_cases"\s*:\s*\[[^\]]*\]\s*\}'
            endpoints = re.findall(endpoint_pattern, json_str, re.DOTALL)
            
            if endpoints:
                # Try to create valid JSON from extracted endpoints
                valid_endpoints = []
                for endpoint_str in endpoints:
                    try:
                        endpoint_obj = json.loads(endpoint_str)
                        valid_endpoints.append(endpoint_obj)
                    except:
                        continue
                
                if valid_endpoints:
                    return {"test_suite": valid_endpoints}
        except:
            pass
        
        # Strategy 5: Return error structure with diagnostic info
        return {
            "test_suite": [{
                "endpoint": "/parsing-error",
                "method": "ERROR",
                "test_cases": [{
                    "name": f"JSON parsing failed: {str(e)}",
                    "type": "error",
                    "error_context": json_str[:100] + "...",
                    "expected_status": 500
                }]
            }]
        }

@app.route('/generate-tests', methods=['POST'])
def generate_tests():
    start_time = time.time()
    errors = []
    test_suite = []
    total_chunks = 0
    processed_chunks = 0
    
    try:
        # Handle request parsing
        try:
            data = request.json
        except Exception as e:
            logger.error(f"Request parsing error: {str(e)}")
            return jsonify({
                "error": "Invalid request format",
                "details": str(e)
            }), 400
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        swagger_url = data.get('swagger_url')
        additional_prompt = data.get('prompt', '')
        
        if not swagger_url:
            return jsonify({"error": "Missing swagger_url"}), 400

        # Fetch and parse Swagger specification
        try:
            swagger_spec = fetch_swagger_spec(swagger_url)
        except Exception as e:
            logger.error(f"Swagger fetch failed: {str(e)}")
            return jsonify({
                "error": "Failed to fetch Swagger spec",
                "details": str(e)
            }), 400
        
        # Chunk endpoints into smaller groups
        endpoint_chunks = chunk_endpoints(swagger_spec, chunk_size=2)
        total_chunks = len(endpoint_chunks)
        
        if total_chunks == 0:
            return jsonify({"error": "No endpoints found in Swagger spec"}), 400
        
        logger.info(f"Processing {total_chunks} chunks")
        
        # Process each chunk
        for i, chunk in enumerate(endpoint_chunks):
            try:
                chunk_start = time.time()
                processed_chunks += 1
                logger.info(f"Processing chunk {i+1}/{total_chunks} with {len(chunk)} endpoints")
                
                # Build prompt for this chunk
                chunk_prompt = build_chunked_prompt(chunk, additional_prompt)
                
                # Call Ollama API with more conservative settings
                ollama_response = session.post(
                    OLLAMA_API_URL,
                    json={
                        "model": "deepseek-r1:7b",
                        "prompt": chunk_prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.0,  # More deterministic
                            "num_ctx": 2048,     # Smaller context
                            "num_predict": 800,  # Smaller response
                            "top_p": 0.9,
                            "repeat_penalty": 1.1
                        }
                    },
                    timeout=60  # Shorter timeout
                )
                ollama_response.raise_for_status()
                
                # Process response
                response_data = ollama_response.json()
                raw_response = response_data.get("response", "").strip()
                
                if not raw_response:
                    logger.warning(f"Chunk {i+1} returned empty response")
                    errors.append(f"Chunk {i+1} returned empty response")
                    continue
                
                # Parse JSON with advanced repair
                test_data = advanced_json_repair(raw_response)
                
                # Validate and add to test suite
                if "test_suite" in test_data and isinstance(test_data["test_suite"], list):
                    # Filter out error structures
                    valid_suites = [
                        suite for suite in test_data["test_suite"] 
                        if not suite.get("endpoint", "").startswith(("/parsing-error", "/json-error"))
                    ]
                    
                    if valid_suites:
                        test_suite.extend(valid_suites)
                        logger.info(f"Chunk {i+1} added {len(valid_suites)} endpoints")
                    else:
                        logger.warning(f"Chunk {i+1} returned only error cases")
                        errors.append(f"Chunk {i+1} generated invalid test cases")
                else:
                    logger.warning(f"Chunk {i+1} returned invalid structure")
                    errors.append(f"Chunk {i+1} returned invalid JSON structure")
                
                logger.info(f"Chunk {i+1} processed in {time.time() - chunk_start:.2f}s")
                
            except requests.exceptions.Timeout:
                logger.warning(f"Chunk {i+1} timed out")
                errors.append(f"Chunk {i+1} timed out")
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                errors.append(f"Chunk {i+1} failed: {str(e)}")
        
        # Calculate final statistics
        total_test_cases = sum(len(suite.get("test_cases", [])) for suite in test_suite)
        
        # Determine status
        if not test_suite:
            status = "failed"
        elif errors:
            status = "partial_success"
        else:
            status = "success"
        
        # Final response
        return jsonify({
            "status": status,
            "test_cases": {"test_suite": test_suite},
            "processing_stats": {
                "total_chunks": total_chunks,
                "processed_chunks": processed_chunks,
                "successful_chunks": processed_chunks - len(errors),
                "failed_chunks": len(errors),
                "total_endpoints": len(test_suite),
                "total_test_cases": total_test_cases,
                "total_time": f"{time.time() - start_time:.2f}s"
            },
            "errors": errors if errors else None
        })
    
    except Exception as e:
        logger.exception(f"Critical error in generate_tests: {str(e)}")
        return jsonify({
            "error": "Test generation failed",
            "details": str(e),
            "processed_chunks": processed_chunks,
            "total_chunks": total_chunks
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Healthcare API Test Generator"
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)