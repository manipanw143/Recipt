# app.py
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logging.basicConfig(level=logging.DEBUG)

# Configuration
SWAGGER_URL = "https://hphmeelan.s3.us-east-1.amazonaws.com/api_docs_86ba43277c.json"
DEEPSEEK_URL = "http://localhost:11434/api/generate"

class TestCaseGenerator:
    def __init__(self):
        self.swagger_data = None
        self.load_swagger_data()
    
    def load_swagger_data(self):
        """Load Swagger/OpenAPI specification"""
        try:
            response = requests.get(SWAGGER_URL)
            response.raise_for_status()
            self.swagger_data = response.json()
            app.logger.info("Swagger data loaded successfully")
        except Exception as e:
            app.logger.error(f"Failed to load Swagger data: {e}")
            self.swagger_data = None
    
    def extract_endpoints(self):
        """Extract endpoint information from Swagger"""
        if not self.swagger_data:
            return []
        
        endpoints = []
        paths = self.swagger_data.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_info = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'responses': details.get('responses', {}),
                        'security': details.get('security', []),
                        'tags': details.get('tags', [])
                    }
                    endpoints.append(endpoint_info)
        
        return endpoints
    
    def generate_test_cases_with_ai(self, prompt, endpoints_data):
        """Generate test cases using Deepseek model"""
        try:
            # Prepare the context for the AI model
            context = f"""
            Based on the following Swagger API documentation and user prompt, generate comprehensive test cases in JSON format.
            
            Swagger Endpoints Data:
            {json.dumps(endpoints_data, indent=2)}
            
            User Prompt: {prompt}
            
            Please generate test cases that include:
            1. Endpoint details (path, method)
            2. Authentication requirements
            3. Test scenarios (positive, negative, edge cases)
            4. Expected responses
            5. Test data
            6. JIRA-style test case descriptions
            
            Return the response in valid JSON format with the following structure:
            {{
                "test_suite": [
                    {{
                        "endpoint": {{
                            "path": "/api/endpoint",
                            "method": "GET",
                            "description": "endpoint description"
                        }},
                        "authentication": {{
                            "required": true,
                            "type": "Bearer Token",
                            "description": "API key required in header"
                        }},
                        "test_cases": [
                            {{
                                "test_id": "TC001",
                                "title": "Valid request test",
                                "description": "Test valid request with proper parameters",
                                "priority": "High",
                                "test_steps": [
                                    "Step 1: Send request with valid parameters",
                                    "Step 2: Verify response status code",
                                    "Step 3: Validate response body"
                                ],
                                "expected_result": "200 OK with valid response data",
                                "test_data": {{}},
                                "preconditions": "User must be authenticated"
                            }}
                        ]
                    }}
                ]
            }}
            """
            
            # Prepare request for Deepseek model
            payload = {
                "model": "deepseek-r1:7b",
                "prompt": context,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(DEEPSEEK_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            ai_response = response.json()
            generated_text = ai_response.get('response', '')
            
            # Try to extract JSON from the response
            try:
                # Find JSON content in the response
                start_idx = generated_text.find('{')
                end_idx = generated_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_content = generated_text[start_idx:end_idx]
                    return json.loads(json_content)
                else:
                    # Fallback: create structured response
                    return self.create_fallback_response(endpoints_data, generated_text)
                    
            except json.JSONDecodeError:
                return self.create_fallback_response(endpoints_data, generated_text)
                
        except Exception as e:
            app.logger.error(f"Error generating test cases: {e}")
            return {"error": f"Failed to generate test cases: {str(e)}"}
    
    def create_fallback_response(self, endpoints_data, ai_text):
        """Create a structured fallback response"""
        test_suite = []
        
        for endpoint in endpoints_data[:3]:  # Limit to first 3 endpoints
            auth_required = len(endpoint.get('security', [])) > 0
            
            test_case = {
                "endpoint": {
                    "path": endpoint['path'],
                    "method": endpoint['method'],
                    "description": endpoint.get('description', endpoint.get('summary', ''))
                },
                "authentication": {
                    "required": auth_required,
                    "type": "Bearer Token" if auth_required else "None",
                    "description": "Authentication required" if auth_required else "No authentication required"
                },
                "test_cases": [
                    {
                        "test_id": f"TC{str(len(test_suite) + 1).zfill(3)}",
                        "title": f"Test {endpoint['method']} {endpoint['path']}",
                        "description": f"Validate {endpoint['method']} request to {endpoint['path']}",
                        "priority": "High",
                        "test_steps": [
                            f"Send {endpoint['method']} request to {endpoint['path']}",
                            "Verify response status code",
                            "Validate response structure"
                        ],
                        "expected_result": "Success response with valid data",
                        "test_data": {},
                        "preconditions": "System should be accessible"
                    }
                ]
            }
            test_suite.append(test_case)
        
        return {
            "test_suite": test_suite,
            "ai_insights": ai_text[:500] if ai_text else "Generated based on Swagger documentation"
        }

# Initialize the test case generator
generator = TestCaseGenerator()

@app.route('/')
def index():
    return render_template('index.html')

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "swagger_loaded": generator.swagger_data is not None,
        "endpoints_count": len(generator.extract_endpoints()) if generator.swagger_data else 0
    })

@app.route('/api/generate-tests', methods=['POST', 'OPTIONS'])
def generate_tests():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Extract endpoints from Swagger
        endpoints = generator.extract_endpoints()
        
        if not endpoints:
            return jsonify({"error": "Failed to load API endpoints from Swagger"}), 500
        
        # Generate test cases using AI
        test_cases = generator.generate_test_cases_with_ai(prompt, endpoints)
        
        return jsonify(test_cases)
        
    except Exception as e:
        app.logger.error(f"Error in generate_tests: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/endpoints', methods=['GET', 'OPTIONS'])
def get_endpoints():
    """Get available endpoints from Swagger"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        endpoints = generator.extract_endpoints()
        return jsonify({"endpoints": endpoints})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Additional debugging route
@app.route('/debug/swagger')
def debug_swagger():
    """Debug route to check swagger data"""
    return jsonify({
        "swagger_loaded": generator.swagger_data is not None,
        "swagger_keys": list(generator.swagger_data.keys()) if generator.swagger_data else [],
        "endpoints_count": len(generator.extract_endpoints())
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)