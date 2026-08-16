from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
import re

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Configuration
# SWAGGER_URL = "https://hphmeelan.s3.us-east-1.amazonaws.com/api_docs_86ba43277c.json"
SWAGGER_URL = "http://202.38.182.170:6400/apispec_1.json"
DEEPSEEK_URL = "http://localhost:11434/api/generate"

# Simplified exclusion list with root tags
EXCLUDED_TAGS = {tag.lower() for tag in [
    "prescription", 
    "content", 
    "email",
    "i18n",
    "upload", 
    "users",
    "permissions",
    "auth"
]}

class TestCaseGenerator:
    def __init__(self):
        self.swagger_url = ""
        self.swagger_data = None

    def load_swagger_data(self):
        if not self.swagger_url:
            return
            
        try:
            response = requests.get(self.swagger_url)
            response.raise_for_status()
            self.swagger_data = response.json()
            app.logger.info(f"Swagger data loaded from {self.swagger_url}")
        except Exception as e:
            app.logger.error(f"Failed to load Swagger data: {e}")
            self.swagger_data = None

    def normalize_tag(self, tag):
        """Remove non-alphanumeric characters and convert to lowercase"""
        return re.sub(r'[^a-z0-9]', '', tag.lower())

    def extract_endpoints(self):
        if not self.swagger_data:
            return []

        endpoints = []
        paths = self.swagger_data.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                # Normalize and process tags
                raw_tags = details.get('tags', [])
                normalized_tags = {self.normalize_tag(tag) for tag in raw_tags}
                
                # Check if any excluded tag is a substring of any normalized tag
                exclude = any(
                    any(excluded_tag in norm_tag for norm_tag in normalized_tags)
                    for excluded_tag in EXCLUDED_TAGS
                )
                
                if not exclude:
                    endpoint_info = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'responses': details.get('responses', {}),
                        'security': details.get('security', []),
                        'tags': list(raw_tags),
                        'requestBody': details.get('requestBody', {}),
                        'operationId': details.get('operationId', '')
                    }
                    endpoints.append(endpoint_info)
                    app.logger.debug(f"Including endpoint: {method.upper()} {path} with tags: {raw_tags}")
                else:
                    app.logger.debug(f"Excluding endpoint: {method.upper()} {path} due to tags: {raw_tags}")

        app.logger.info(f"Total endpoints after filtering: {len(endpoints)}")
        return endpoints

    def extract_schema_properties(self, schema_ref, components):
        """Extract properties from schema reference"""
        if not schema_ref or not components:
            return {}
        
        # Handle $ref
        if isinstance(schema_ref, dict) and '$ref' in schema_ref:
            ref_path = schema_ref['$ref'].split('/')[-1]
            schema = components.get('schemas', {}).get(ref_path, {})
        else:
            schema = schema_ref
        
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])

        return {
            'properties': properties,
            'required': required_fields,
            'schema': schema
        }

    def generate_test_data_from_schema(self, properties, required_fields):
        """Generate realistic test data based on schema properties"""
        test_data = {}
        
        for field, field_schema in properties.items():
            field_type = field_schema.get('type', 'string')
            field_format = field_schema.get('format', '')
            field_example = field_schema.get('example')
            field_enum = field_schema.get('enum', [])
            
            # Use example if available
            if field_example:
                test_data[field] = field_example
            elif field_enum:
                test_data[field] = field_enum[0]
            elif field_type == 'string':
                if field_format == 'email':
                    test_data[field] = "test@example.com"
                elif field_format == 'date':
                    test_data[field] = "2024-01-01"
                elif field_format == 'date-time':
                    test_data[field] = "2024-01-01T10:00:00Z"
                elif 'password' in field.lower():
                    test_data[field] = "SecurePass123!"
                elif 'name' in field.lower():
                    test_data[field] = "John Doe"
                elif 'phone' in field.lower():
                    test_data[field] = "+1234567890"
                else:
                    test_data[field] = f"test_{field}"
            elif field_type == 'integer':
                min_val = field_schema.get('minimum', 1)
                max_val = field_schema.get('maximum', 100)
                test_data[field] = min_val if min_val else 1
            elif field_type == 'number':
                test_data[field] = 10.5
            elif field_type == 'boolean':
                test_data[field] = True
            elif field_type == 'array':
                items_schema = field_schema.get('items', {})
                if items_schema.get('type') == 'string':
                    test_data[field] = ["item1", "item2"]
                else:
                    test_data[field] = [1, 2, 3]
            else:
                test_data[field] = f"test_{field}"
        
        return test_data

    def generate_invalid_test_data(self, properties, required_fields):
        """Generate invalid test data for negative testing"""
        invalid_scenarios = []
        
        # Missing required fields
        if required_fields:
            for req_field in required_fields:
                invalid_data = self.generate_test_data_from_schema(properties, required_fields)
                if req_field in invalid_data:
                    del invalid_data[req_field]
                invalid_scenarios.append({
                    'data': invalid_data,
                    'description': f'Missing required field: {req_field}',
                    'expected_error': f'Field {req_field} is required'
                })
        
        # Invalid data types
        for field, field_schema in properties.items():
            field_type = field_schema.get('type', 'string')
            invalid_data = self.generate_test_data_from_schema(properties, required_fields)
            
            if field_type == 'integer':
                invalid_data[field] = "not_a_number"
                invalid_scenarios.append({
                    'data': invalid_data,
                    'description': f'Invalid data type for {field} (string instead of integer)',
                    'expected_error': f'Field {field} must be an integer'
                })
            elif field_type == 'string' and field_schema.get('format') == 'email':
                invalid_data[field] = "invalid_email"
                invalid_scenarios.append({
                    'data': invalid_data,
                    'description': f'Invalid email format for {field}',
                    'expected_error': f'Field {field} must be a valid email'
                })
        
        return invalid_scenarios[:3]  # Limit to 3 scenarios

    def create_swagger_based_response(self, endpoints_data, user_prompt=""):
        """Create test cases based on actual Swagger API specifications"""
        test_suite = []
        components = self.swagger_data.get('components', {}) if self.swagger_data else {}
        
        for i, endpoint in enumerate(endpoints_data):
            test_cases = []
            base_id = f"TC{str(i+1).zfill(3)}"
            
            # Extract request body schema if available
            request_body = endpoint.get('requestBody', {})
            request_schema = {}
            if request_body:
                content = request_body.get('content', {})
                json_content = content.get('application/json', {})
                if json_content:
                    request_schema = self.extract_schema_properties(
                        json_content.get('schema', {}), components
                    )
            
            # Extract path parameters
            path_params = [p for p in endpoint.get('parameters', []) if p.get('in') == 'path']
            query_params = [p for p in endpoint.get('parameters', []) if p.get('in') == 'query']
            
            # Generate positive test case
            positive_test_data = {}
            if request_schema.get('properties'):
                positive_test_data = self.generate_test_data_from_schema(
                    request_schema['properties'], 
                    request_schema.get('required', [])
                )
            
            # Add path parameters to test data
            for param in path_params:
                param_name = param.get('name', '')
                param_type = param.get('schema', {}).get('type', 'string')
                if param_type == 'integer':
                    positive_test_data[param_name] = 1
                else:
                    positive_test_data[param_name] = f"test_{param_name}"
            
            # Determine expected response codes
            responses = endpoint.get('responses', {})
            success_codes = [code for code in responses.keys() if code.startswith('2')]
            error_codes = [code for code in responses.keys() if code.startswith('4') or code.startswith('5')]
            
            # Positive test case
            test_cases.append({
                "test_id": f"{base_id}_001",
                "title": f"Verify successful {endpoint['method']} {endpoint['path']}",
                "description": endpoint.get('summary', f"Test {endpoint['method']} operation on {endpoint['path']}"),
                "test_category": "Functional Testing",
                "test_type": "Positive Testing",
                "priority": "High",
                "test_steps": self.generate_test_steps(endpoint, positive_test_data, "positive"),
                "expected_result": f"API returns {success_codes[0] if success_codes else '200'} status code with valid response structure",
                "test_data": {
                    "method": endpoint['method'],
                    "endpoint": endpoint['path'],
                    "request_body": positive_test_data if positive_test_data else None,
                    "headers": {"Content-Type": "application/json"},
                    "expected_status": success_codes[0] if success_codes else "200"
                },
                "preconditions": self.generate_preconditions(endpoint),
                "postconditions": f"Data is processed according to {endpoint['method']} operation requirements"
            })
            
            # Generate negative test cases based on actual schema
            if request_schema.get('properties'):
                invalid_scenarios = self.generate_invalid_test_data(
                    request_schema['properties'], 
                    request_schema.get('required', [])
                )
                
                for j, scenario in enumerate(invalid_scenarios):
                    test_cases.append({
                        "test_id": f"{base_id}_00{j+2}",
                        "title": f"Verify {endpoint['method']} {endpoint['path']} - {scenario['description']}",
                        "description": f"Validate error handling for {scenario['description']}",
                        "test_category": "Functional Testing",
                        "test_type": "Negative Testing",
                        "priority": "Medium",
                        "test_steps": self.generate_test_steps(endpoint, scenario['data'], "negative"),
                        "expected_result": f"API returns {error_codes[0] if error_codes else '400'} with appropriate error message",
                        "test_data": {
                            "method": endpoint['method'],
                            "endpoint": endpoint['path'],
                            "request_body": scenario['data'],
                            "headers": {"Content-Type": "application/json"},
                            "expected_status": error_codes[0] if error_codes else "400",
                            "expected_error": scenario['expected_error']
                        },
                        "preconditions": self.generate_preconditions(endpoint),
                        "postconditions": "System should maintain data integrity and return descriptive error"
                    })
            
            # Authentication requirement
            auth_required = len(endpoint.get('security', [])) > 0
            
            suite_item = {
                "endpoint": {
                    "path": endpoint['path'],
                    "method": endpoint['method'],
                    "description": endpoint.get('description', endpoint.get('summary', 'No description available')),
                    "operation_id": endpoint.get('operationId', ''),
                    "tags": endpoint.get('tags', [])
                },
                "test_category": "Functional Testing",
                "authentication": {
                    "required": auth_required,
                    "type": "Bearer Token" if auth_required else "None",
                    "description": "Authentication required as per security configuration" if auth_required else "No authentication required"
                },
                "request_schema": request_schema.get('schema', {}),
                "response_codes": list(responses.keys()),
                "test_cases": test_cases
            }
            test_suite.append(suite_item)
        
        return {
            "test_suite": test_suite,
            "summary": {
                "total_test_cases": sum(len(suite["test_cases"]) for suite in test_suite),
                "total_endpoints": len(test_suite),
                "test_categories": ["Functional Testing"],
                "focus": "API Functional Validation Based on Swagger Specification",
                "coverage_areas": [
                    "Request/Response Validation",
                    "Schema Compliance",
                    "Business Logic Validation",
                    "Error Handling",
                    "Authentication & Authorization",
                    "Input Validation",
                    "Data Type Validation"
                ]
            },
            "swagger_analysis": {
                "base_url": self.swagger_data.get('servers', [{}])[0].get('url', '') if self.swagger_data else '',
                "api_version": self.swagger_data.get('info', {}).get('version', '') if self.swagger_data else '',
                "total_paths": len(self.swagger_data.get('paths', {})) if self.swagger_data else 0,
                "components_count": len(self.swagger_data.get('components', {}).get('schemas', {})) if self.swagger_data else 0
            },
            "user_prompt": user_prompt
        }

    def generate_test_steps(self, endpoint, test_data, test_type):
        """Generate detailed test steps based on endpoint and data"""
        steps = []
        
        if test_type == "positive":
            steps.append("1. Verify API service is accessible and running")
            if endpoint.get('security'):
                steps.append("2. Obtain valid authentication token")
                steps.append("3. Set authorization header with valid token")
            
            if test_data:
                steps.append(f"4. Prepare valid test data: {json.dumps(test_data, indent=2)}")
            
            steps.append(f"5. Send {endpoint['method']} request to {endpoint['path']}")
            steps.append("6. Verify response status code indicates success (2xx)")
            steps.append("7. Validate response body structure matches expected schema")
            steps.append("8. Verify all required response fields are present")
            steps.append("9. Check data types and formats in response")
            
        else:  # negative
            steps.append("1. Verify API service is accessible and running")
            if endpoint.get('security'):
                steps.append("2. Obtain valid authentication token (if required)")
            
            steps.append(f"3. Prepare invalid test data: {json.dumps(test_data, indent=2)}")
            steps.append(f"4. Send {endpoint['method']} request to {endpoint['path']} with invalid data")
            steps.append("5. Verify response status code indicates error (4xx)")
            steps.append("6. Validate error response structure")
            steps.append("7. Verify descriptive error message is returned")
            steps.append("8. Confirm no unintended side effects occurred")
        
        return steps

    def generate_preconditions(self, endpoint):
        """Generate preconditions based on endpoint requirements"""
        preconditions = ["API service is running and accessible"]
        
        if endpoint.get('security'):
            preconditions.append("Valid authentication credentials are available")
        
        # Check for path parameters
        path_params = [p for p in endpoint.get('parameters', []) if p.get('in') == 'path']
        if path_params:
            preconditions.append("Required path parameters are identified")
        
        # Check for required query parameters
        required_query_params = [
            p for p in endpoint.get('parameters', []) 
            if p.get('in') == 'query' and p.get('required', False)
        ]
        if required_query_params:
            preconditions.append("Required query parameters are available")
        
        return "; ".join(preconditions)

    def generate_enhanced_prompt(self, user_prompt, endpoints_data):
        """Generate an enhanced prompt for better AI response"""
        
        # Extract endpoint summaries for context
        endpoint_summaries = []
        for endpoint in endpoints_data[:10]:  # Limit to first 10 for brevity
            summary = f"{endpoint['method']} {endpoint['path']}"
            if endpoint.get('summary'):
                summary += f" - {endpoint['summary']}"
            endpoint_summaries.append(summary)
        
        enhanced_prompt = f"""
        You are an expert QA engineer tasked with creating comprehensive FUNCTIONAL test cases based on Swagger API documentation.

        **IMPORTANT INSTRUCTIONS:**
        1. Generate ONLY FUNCTIONAL test cases (no performance, security, or load testing)
        2. All test cases must be categorized under "Functional Testing"
        3. Focus on business logic validation, data integrity, and API behavior
        4. Include positive, negative, and edge case scenarios
        5. Provide detailed test steps and expected results
        6. Use proper JIRA-style test case format
        7. Base test cases on ACTUAL API specifications, not generic templates

        **USER REQUEST:**
        {user_prompt}

        **AVAILABLE API ENDPOINTS:**
        {chr(10).join(endpoint_summaries)}

        **SWAGGER API DOCUMENTATION:**
        {json.dumps(endpoints_data, indent=2)}

        Generate comprehensive functional test cases that thoroughly validate the API behavior and business logic based on the actual Swagger specification provided.
        """
        
        return enhanced_prompt

    def generate_test_cases_with_ai(self, prompt, endpoints_data):
        try:
            # First, try to generate AI-enhanced test cases
            enhanced_prompt = self.generate_enhanced_prompt(prompt, endpoints_data)
            
            payload = {
                "model": "deepseek-r1:7b",
                "prompt": enhanced_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 3000,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }

            try:
                response = requests.post(DEEPSEEK_URL, json=payload, timeout=90)
                response.raise_for_status()
                ai_response = response.json()
                generated_text = ai_response.get('response', '')

                # Try to extract JSON from AI response
                start_idx = generated_text.find('{')
                end_idx = generated_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_content = generated_text[start_idx:end_idx]
                    parsed_response = json.loads(json_content)
                    
                    # Ensure all test cases are marked as functional
                    self.ensure_functional_categorization(parsed_response)
                    parsed_response['ai_generated'] = True
                    parsed_response['ai_insights'] = generated_text[:500]
                    return parsed_response
            except Exception as ai_error:
                app.logger.warning(f"AI generation failed: {ai_error}, falling back to Swagger-based generation")
            
            # Fallback to Swagger-based generation (this is the main improvement)
            swagger_response = self.create_swagger_based_response(endpoints_data, prompt)
            swagger_response['ai_generated'] = False
            swagger_response['generation_method'] = 'swagger_based'
            return swagger_response
            
        except Exception as e:
            app.logger.error(f"Error generating test cases: {e}")
            return {"error": f"Failed to generate test cases: {str(e)}"}

    def ensure_functional_categorization(self, response):
        """Ensure all test cases are categorized as functional testing"""
        if 'test_suite' in response:
            for suite in response['test_suite']:
                suite['test_category'] = 'Functional Testing'
                if 'test_cases' in suite:
                    for test_case in suite['test_cases']:
                        test_case['test_category'] = 'Functional Testing'
                        # Ensure test_type is functional-related
                        if 'test_type' not in test_case:
                            test_case['test_type'] = 'Positive Testing'
                                    
        # Update summary to reflect functional testing focus
        if 'summary' not in response:
            response['summary'] = {}
        response['summary']['test_categories'] = ['Functional Testing']
        response['summary']['focus'] = 'API Functional Validation'

    # Keep the old method for backward compatibility but rename it
    def create_fallback_response(self, endpoints_data, ai_text):
        """Legacy fallback method - now redirects to Swagger-based generation"""
        return self.create_swagger_based_response(endpoints_data, ai_text)

generator = TestCaseGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "swagger_loaded": generator.swagger_data is not None,
        "endpoints_count": len(generator.extract_endpoints()) if generator.swagger_data else 0
    })

@app.route('/api/generate-tests', methods=['POST', 'OPTIONS'])
def generate_tests():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        endpoints = generator.extract_endpoints()
        if not endpoints:
            return jsonify({"error": "Failed to load API endpoints from Swagger"}), 500

        test_cases = generator.generate_test_cases_with_ai(prompt, endpoints)
        return jsonify(test_cases)
        
    except Exception as e:
        app.logger.error(f"Error in generate_tests: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    try:
        endpoints = generator.extract_endpoints()
        return jsonify({
            "endpoints": endpoints,
            "total_count": len(endpoints),
            "excluded_tags": list(EXCLUDED_TAGS)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load-swagger', methods=['POST'])
def load_swagger():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Update the generator with new URL
        generator.swagger_url = url
        generator.load_swagger_data()  # Reload with new URL
        
        endpoints = generator.extract_endpoints()
        return jsonify({
            "status": "Swagger documentation loaded successfully",
            "endpoints_count": len(endpoints),
            "endpoints": endpoints
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample-prompts', methods=['GET'])
def get_sample_prompts():
    """Provide sample prompts for functional testing"""
    sample_prompts = [
        {
            "title": "User Management Functional Tests",
            "prompt": "Generate comprehensive functional test cases for user management APIs including user registration, profile updates, user retrieval, and account deactivation. Focus on input validation, business rule verification, and proper error handling for invalid data scenarios."
        },
        {
            "title": "Data CRUD Operations Testing",
            "prompt": "Create functional test cases for Create, Read, Update, and Delete operations on core business entities. Include tests for data integrity, field validation, required field checking, and proper status code responses for each operation."
        },
        {
            "title": "Authentication & Authorization Flow",
            "prompt": "Generate functional test cases for authentication endpoints including login, logout, token refresh, and password reset flows. Validate proper authentication responses, token handling, and access control for protected resources."
        },
        {
            "title": "Business Logic & Workflow Validation",
            "prompt": "Create test cases that validate complex business workflows and rules. Include state transitions, conditional logic processing, and multi-step operations. Focus on ensuring business requirements are properly implemented."
        },
        {
            "title": "Input Validation & Error Handling",
            "prompt": "Generate comprehensive test cases for input validation including boundary values, data type validation, required field checking, format validation, and proper error response handling for various invalid input scenarios."
        }
    ]
    
    return jsonify({"sample_prompts": sample_prompts})

@app.route('/debug/swagger')
def debug_swagger():
    return jsonify({
        "swagger_loaded": generator.swagger_data is not None,
        "swagger_keys": list(generator.swagger_data.keys()) if generator.swagger_data else [],
        "endpoints_count": len(generator.extract_endpoints()),
        "excluded_tags": list(EXCLUDED_TAGS)
    })

@app.route('/debug/tags')
def debug_tags():
    if not generator.swagger_data:
        return jsonify({"error": "Swagger data not loaded"})
    
    all_tags = set()
    endpoint_details = []
    paths = generator.swagger_data.get('paths', {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                continue
                
            raw_tags = details.get('tags', [])
            normalized_tags = {generator.normalize_tag(tag) for tag in raw_tags}
            all_tags.update(normalized_tags)
            
            # Check exclusion
            exclude = any(
                any(excluded_tag in norm_tag for norm_tag in normalized_tags)
                for excluded_tag in EXCLUDED_TAGS
            )
            
            endpoint_details.append({
                "path": path,
                "method": method.upper(),
                "original_tags": raw_tags,
                "normalized_tags": list(normalized_tags),
                "is_excluded": exclude,
                "reason": "Has excluded tags" if exclude else "No excluded tags found"
            })
    
    return jsonify({
        "all_tags_in_swagger": sorted(list(all_tags)),
        "excluded_tags": list(EXCLUDED_TAGS),
        "tags_being_filtered": sorted(list(EXCLUDED_TAGS)),
        "endpoint_details": endpoint_details,
        "total_endpoints": len(endpoint_details),
        "excluded_endpoints": len([ep for ep in endpoint_details if ep["is_excluded"]]),
        "included_endpoints": len([ep for ep in endpoint_details if not ep["is_excluded"]])
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)