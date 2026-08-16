# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
SWAGGER_URL = os.getenv('SWAGGER_URL', "https://hphmeelan.s3.us-east-1.amazonaws.com/api_docs_86ba43277c.json")
OLLAMA_URL = os.getenv('OLLAMA_URL', "http://localhost:11434/api/generate")
STRAPI_BASE_URL = os.getenv('STRAPI_BASE_URL', "http://localhost:1337")
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))  # 5 minutes

# Global cache variables
swagger_cache = None
last_fetch_time = 0

def fetch_swagger_data():
    """Fetch and cache Swagger documentation"""
    global swagger_cache, last_fetch_time
    
    current_time = time.time()
    if not swagger_cache or (current_time - last_fetch_time) > CACHE_TIMEOUT:
        try:
            response = requests.get(SWAGGER_URL, timeout=10)
            response.raise_for_status()
            swagger_cache = response.json()
            last_fetch_time = current_time
            app.logger.info("Swagger cache updated")
        except Exception as e:
            app.logger.error(f"Failed to fetch Swagger: {str(e)}")
            raise RuntimeError(f"Failed to fetch API documentation: {str(e)}")
    
    return swagger_cache

def parse_endpoints(swagger_data):
    """Extract endpoints from Swagger specification"""
    try:
        endpoints = []
        base_path = swagger_data.get('basePath', '')
        servers = swagger_data.get('servers', [{'url': STRAPI_BASE_URL}])
        base_url = servers[0]['url'] if servers else STRAPI_BASE_URL
        
        for path, methods in swagger_data.get('paths', {}).items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoint = {
                        'path': base_path + path,
                        'method': method.upper(),
                        'full_url': base_url + base_path + path,
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'requestBody': details.get('requestBody', {}),
                        'responses': details.get('responses', {}),
                        'security': details.get('security', [])
                    }
                    endpoints.append(endpoint)
        return endpoints
    except Exception as e:
        app.logger.error(f"Error parsing endpoints: {str(e)}")
        raise RuntimeError(f"Invalid Swagger format: {str(e)}")



def generate_test_prompt(endpoint, test_type='functional'):
    """Create optimized prompt for test generation - FIXED PROMPT"""
    try:
        # Clean up and format parameters
        parameters = json.dumps(endpoint.get('parameters', []), indent=2) if endpoint.get('parameters') else "None"
        
        # Clean up request body
        request_body = endpoint.get('requestBody', {})
        if 'content' in request_body and 'application/json' in request_body['content']:
            request_body = json.dumps(request_body['content']['application/json']['schema'], indent=2)
        else:
            request_body = "None"
        
        # Clean up responses
        responses = json.dumps(endpoint.get('responses', {}), indent=2) if endpoint.get('responses') else "None"
        
        return f"""
        Generate 5 functional test cases in JSON format for this API endpoint:
        - Method: {endpoint['method']}
        - Path: {endpoint['path']}
        - Full URL: {endpoint['full_url']}
        - Parameters: {parameters}
        - Request Body Schema: {request_body}
        - Responses: {responses}
        
        Output structure:
        {{
            "endpoint": "string",
            "testType": "functional",
            "tests": [
                {{
                    "name": "Test name",
                    "method": "HTTP_METHOD",
                    "url": "full_url",
                    "body": {{ ... }},
                    "expectedStatus": 200,
                    "validationRules": ["status_code", "response_time_ms"]
                }}
            ]
        }}
        
        Important: 
        - Include 3 positive and 2 negative test cases
        - Use realistic test data
        - Output ONLY valid JSON with no extra text
        """
    except Exception as e:
        logging.error(f"Error creating prompt: {str(e)}")
        raise RuntimeError("Failed to create test generation prompt")

def generate_tests_with_ollama(endpoint, test_type='functional'):
    """Generate tests using Ollama API - FIXED JSON PARSING"""
    try:
        prompt = generate_test_prompt(endpoint, test_type)
        logging.info(f"Sending prompt to Ollama: {prompt[:500]}...")
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "deepseek-r1",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3},
                "format": "json"  # Explicitly request JSON format
            },
            timeout=120
        )
        response.raise_for_status()
        
        # Extract JSON from response
        response_data = response.json()
        response_text = response_data.get('response', '')
        
        # Improved JSON extraction
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            logging.error(f"No JSON found in response: {response_text[:500]}")
            raise ValueError("No JSON found in Ollama response")
            
        json_str = json_match.group()
        return json.loads(json_str)
        
    except Exception as e:
        logging.error(f"Test generation failed: {str(e)}")
        raise RuntimeError(f"Test generation failed: {str(e)}")

def execute_single_test(test):
    """Execute a single test case and return results"""
    start_time = time.time()
    result = {
        'name': test['name'],
        'status': 'FAIL',
        'duration': 0,
        'error': None,
        'response': None
    }
    
    try:
        # Prepare request
        headers = test.get('headers', {})
        data = test.get('body', None)
        
        # Make request
        response = requests.request(
            method=test['method'],
            url=test['url'],
            headers=headers,
            json=data if data else None,
            timeout=10
        )
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to ms
        result['duration'] = round(duration, 2)
        result['response'] = {
            'status': response.status_code,
            'body': response.json() if response.content else None
        }
        
        # Validate response
        if response.status_code != test['expectedStatus']:
            raise ValueError(f"Expected status {test['expectedStatus']}, got {response.status_code}")
        
        # Additional validations
        validation_rules = test.get('validationRules', [])
        if 'response_time_ms' in validation_rules and duration > 1000:
            raise ValueError(f"Slow response: {duration:.2f}ms")
            
        if 'error_message' in validation_rules and test['expectedStatus'] >= 400:
            response_data = response.json()
            if 'error' not in response_data and 'message' not in response_data:
                raise ValueError("Missing error message in response")
        
        # Test passed
        result['status'] = 'PASS'
        
    except requests.exceptions.RequestException as e:
        result['error'] = f"Request failed: {str(e)}"
    except ValueError as e:
        result['error'] = str(e)
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result

# API Endpoints
@app.route('/api/endpoints', methods=['POST'])
def get_endpoints():
    """Fetch and return all API endpoints from Swagger"""
    try:
        swagger_data = fetch_swagger_data()
        endpoints = parse_endpoints(swagger_data)
        return jsonify({
            'status': 'success',
            'count': len(endpoints),
            'endpoints': endpoints
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/generate-tests', methods=['POST'])
def generate_tests():
    """Generate tests for a specific endpoint"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        test_type = data.get('testType', 'functional')
        
        if not endpoint:
            return jsonify({
                'status': 'error',
                'message': 'Missing endpoint data'
            }), 400
        
        tests = generate_tests_with_ollama(endpoint, test_type)
        return jsonify({
            'status': 'success',
            'tests': tests
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/execute-tests', methods=['POST'])
def execute_tests():
    """Execute a list of test cases"""
    try:
        data = request.get_json()
        tests = data.get('tests', [])
        
        if not tests:
            return jsonify({
                'status': 'error',
                'message': 'No tests provided'
            }), 400
        
        results = []
        for test in tests:
            results.append(execute_single_test(test))
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)