from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
from urllib.parse import urljoin, urlparse

app = Flask(__name__)
CORS(app)

class K6ScriptGenerator:
    def __init__(self):
        self.swagger_data = None
        self.base_url = ""
        
    def fetch_swagger_data(self, swagger_url):
        """Fetch and parse Swagger JSON data"""
        
        try:
            response = requests.get(swagger_url, timeout=30)
            response.raise_for_status()
            self.swagger_data = response.json()

            # Extract base URL from swagger
            if 'servers' in self.swagger_data and self.swagger_data['servers']:
                self.base_url = self.swagger_data['servers'][0]['url']
            elif 'host' in self.swagger_data:
                scheme = self.swagger_data.get('schemes', ['https'])[0]
                base_path = self.swagger_data.get('basePath', '')
                self.base_url = f"{scheme}://{self.swagger_data['host']}{base_path}"
            
            return True
        except Exception as e:
            raise Exception(f"Failed to fetch Swagger data: {str(e)}")
    
    def generate_ai_enhanced_script(self, model_url, model_name, test_config):
        """Generate K6 script using AI model for intelligent test data"""
        
        # Prepare prompt for AI model
        prompt = self._create_ai_prompt(test_config)
        
        try:
            # Call AI model
            ai_response = requests.post(model_url, json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            }, timeout=60)

            if ai_response.status_code == 200:
                ai_suggestions = ai_response.json().get('response', '')
            else:
                ai_suggestions = "// AI model not available, using default test data"
                
        except Exception as e:
            ai_suggestions = f"// AI model error: {str(e)}"
        
        # Generate the main K6 script
        script = self._generate_k6_script(test_config, ai_suggestions)
        return script
    
    def _create_ai_prompt(self, test_config):
        """Create prompt for AI model to generate intelligent test data"""
        endpoints_info = []
        
        if self.swagger_data and 'paths' in self.swagger_data:
            for path, methods in self.swagger_data['paths'].items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoint_info = {
                            'path': path,
                            'method': method.upper(),
                            'summary': details.get('summary', ''),
                            'parameters': details.get('parameters', []),
                            'requestBody': details.get('requestBody', {}),
                            'responses': details.get('responses', {})
                        }
                        endpoints_info.append(endpoint_info)
        
        prompt = f"""
        Generate realistic test data and scenarios for K6 performance testing based on the following API endpoints:

        API Endpoints:
        {json.dumps(endpoints_info, indent=2)}

        Requirements:
        1. Suggest realistic test data for request bodies and parameters
        2. Identify which endpoints should be tested with higher priority
        3. Suggest realistic user scenarios and test flows
        4. Provide examples of edge cases to test
        5. Suggest appropriate response validation checks

        Please provide your suggestions in a structured format that can be easily parsed and integrated into K6 test scripts.
        """
        
        return prompt
    
    def _generate_k6_script(self, test_config, ai_suggestions=""):
        """Generate the complete K6 performance test script"""
        
        if not self.swagger_data:
            raise Exception("No Swagger data available")
        
        # Extract base URL
        base_url = test_config.get('baseUrl') or self.base_url or 'http://localhost:8000'
        
        script_parts = []
        
        # Script header and imports
        script_parts.append(self._generate_script_header())
        
        # Test configuration
        script_parts.append(self._generate_test_options(test_config))
        
        # Helper functions
        script_parts.append(self._generate_helper_functions())
        
        # Test data and scenarios
        script_parts.append(self._generate_test_data(ai_suggestions))
        
        # Setup function
        script_parts.append(self._generate_setup_function())
        
        # Main test function
        script_parts.append(self._generate_main_test_function(base_url, test_config))
        
        # Individual endpoint test functions
        script_parts.append(self._generate_endpoint_functions(base_url, test_config))
        
        # Teardown function
        script_parts.append(self._generate_teardown_function())
        
        return '\n\n'.join(script_parts)
    
    def _generate_script_header(self):
        """Generate K6 script header with imports"""
        return '''import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time', true);
const requestCounter = new Counter('requests_total');'''
    
    def _generate_test_options(self, test_config):
        """Generate K6 test options"""
        return f'''// Test configuration
export const options = {{
    vus: {test_config.get('vus', 10)},
    duration: '{test_config.get('duration', '30s')}',
    stages: [
        {{ duration: '{test_config.get('rampUp', '10s')}', target: {test_config.get('vus', 10)} }},
        {{ duration: '{test_config.get('duration', '30s')}', target: {test_config.get('vus', 10)} }},
        {{ duration: '{test_config.get('rampDown', '10s')}', target: 0 }},
    ],
    thresholds: {{
        http_req_duration: ['p(95)<2000', 'p(99)<5000'],
        http_req_failed: ['rate<0.1'],
        error_rate: ['rate<0.1'],
        checks: ['rate>0.9'],
    }},
}};'''
    
    def _generate_helper_functions(self):
        """Generate helper functions"""
        return '''// Helper functions
function getAuthHeaders() {
    return {
        'Authorization': 'Bearer ' + (__ENV.AUTH_TOKEN || 'your_auth_token_here'),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    };
}

function logResponse(response, endpoint) {
    console.log(`${endpoint}: ${response.status} - ${response.timings.duration}ms`);
    
    if (response.status >= 400) {
        console.log(`Error response body: ${response.body}`);
    }
}

function validateResponse(response, expectedStatus = 200) {
    const isValid = check(response, {
        [`Status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
        'Response time < 2000ms': (r) => r.timings.duration < 2000,
        'Response has body': (r) => r.body.length > 0,
    });
    
    errorRate.add(!isValid);
    responseTime.add(response.timings.duration);
    requestCounter.add(1);
    
    return isValid;
}'''
    
    def _generate_test_data(self, ai_suggestions):
        """Generate test data section"""
        test_data = '''// Test data
const testData = {
    users: [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
        { id: 3, name: 'Bob Johnson', email: 'bob@example.com' },
    ],
    products: [
        { id: 1, name: 'Product A', price: 29.99 },
        { id: 2, name: 'Product B', price: 49.99 },
        { id: 3, name: 'Product C', price: 19.99 },
    ],
    orders: [
        { id: 1, userId: 1, productId: 1, quantity: 2 },
        { id: 2, userId: 2, productId: 2, quantity: 1 },
    ],
};

function getRandomTestData(type) {
    const data = testData[type];
    return data ? data[Math.floor(Math.random() * data.length)] : {};
}

function generateRandomPayload(schema = {}) {
    return {
        id: randomIntBetween(1, 1000),
        name: randomString(10),
        email: `user${randomIntBetween(1, 1000)}@example.com`,
        timestamp: new Date().toISOString(),
        ...schema
    };
}'''
        
        if ai_suggestions and "AI model error:" not in ai_suggestions:
            test_data += f'''

// AI-generated suggestions:
/*
{ai_suggestions}
*/'''
        
        return test_data
    
    def _generate_setup_function(self):
        """Generate setup function"""
        return '''// Setup function - runs once before all VUs
export function setup() {
    console.log('Starting performance test...');
    console.log(`Test will run with ${__ENV.K6_VUS || options.vus} virtual users`);
    
    // You can perform authentication or data setup here
    return {
        authToken: __ENV.AUTH_TOKEN || 'default_token',
        baseUrl: __ENV.BASE_URL || '',
    };
}'''
    
    def _generate_main_test_function(self, base_url, test_config):
        """Generate main test function"""
        endpoints = self._extract_endpoints()
        
        test_calls = []
        for endpoint in endpoints[:10]:  # Limit to first 10 endpoints
            func_name = self._get_function_name(endpoint['path'], endpoint['method'])
            test_calls.append(f"            {func_name}(baseUrl, headers);")
        
        test_calls_str = '\n'.join(test_calls) if test_calls else "            console.log('No endpoints to test');"
        
        return f'''// Main test function
export default function(data) {{
    const baseUrl = data?.baseUrl || '{base_url}';
    const headers = getAuthHeaders();
    
    group('API Performance Test', () => {{
        // Test critical user journeys
        group('User Journey 1 - Basic Operations', () => {{
{test_calls_str}
        }});
        
        // Add more test groups as needed
        group('Load Test - Random Endpoints', () => {{
            const endpoints = [{', '.join([f'"{ep["path"]}"' for ep in endpoints[:5]])}];
            const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
            
            const response = http.get(`${{baseUrl}}${{randomEndpoint}}`, {{ headers }});
            validateResponse(response);
        }});
    }});
    
    // Random sleep between 1-3 seconds to simulate user behavior
    sleep(randomIntBetween(1, 3));
}}'''
    
    def _generate_endpoint_functions(self, base_url, test_config):
        """Generate individual endpoint test functions"""
        endpoints = self._extract_endpoints()
        functions = []
        
        for endpoint in endpoints:
            func_code = self._generate_endpoint_function(endpoint, test_config)
            functions.append(func_code)
        
        return '\n\n'.join(functions)
    
    def _generate_endpoint_function(self, endpoint, test_config):
        """Generate function for a specific endpoint"""
        func_name = self._get_function_name(endpoint['path'], endpoint['method'])
        method = endpoint['method'].lower()
        path = endpoint['path']
        
        # Replace path parameters with dynamic values
        path_with_params = re.sub(r'\{([^}]+)\}', r'${randomIntBetween(1, 100)}', path)
        
        params = ''
        body = ''
        
        if method in ['post', 'put', 'patch']:
            if endpoint.get('requestBody'):
                body = '''
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);'''
                params = ', { headers, body }'
            else:
                params = ', { headers }'
        else:
            params = ', { headers }'
        
        return f'''function {func_name}(baseUrl, headers) {{
    const url = `${{baseUrl}}{path_with_params}`;{body}
    
    const response = http.{method}(url{params});
    
    const isValid = validateResponse(response);
    logResponse(response, '{method.upper()} {path}');
    
    if (!isValid) {{
        console.warn(`Failed request to {path}`);
    }}
    
    return response;
}}'''
    
    def _generate_teardown_function(self):
        """Generate teardown function"""
        return '''// Teardown function - runs once after all VUs complete
export function teardown(data) {
    console.log('Performance test completed!');
    console.log('Check the results for detailed metrics.');
    
    // Cleanup operations can be performed here
}'''
    
    def _extract_endpoints(self):
        """Extract endpoints from Swagger data"""
        endpoints = []
        
        if not self.swagger_data or 'paths' not in self.swagger_data:
            return endpoints
        
        for path, methods in self.swagger_data['paths'].items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'parameters': details.get('parameters', []),
                        'requestBody': details.get('requestBody', {}),
                        'responses': details.get('responses', {})
                    })
        
        return endpoints
    
    def _get_function_name(self, path, method):
        """Generate function name from path and method"""
        # Clean path and create function name
        clean_path = re.sub(r'[^a-zA-Z0-9]', '_', path.strip('/'))
        clean_path = re.sub(r'_+', '_', clean_path).strip('_')
        
        if not clean_path:
            clean_path = 'root'
        
        return f"test_{method.lower()}_{clean_path}"

# Initialize the generator
generator = K6ScriptGenerator()

@app.route('/api/generate-k6-script', methods=['POST'])
def generate_k6_script():
    try:
        data = request.get_json()
        
        swagger_url = data.get('swagger_url')
        model_url = data.get('model_url')
        model_name = data.get('model_name')
        test_config = data.get('test_config', {})
        
        if not swagger_url:
            return jsonify({'error': 'Swagger URL is required'}), 400
        
        # Fetch Swagger data
        generator.fetch_swagger_data(swagger_url)
        
        # Generate K6 script with AI enhancement
        if model_url and model_name:
            k6_script = generator.generate_ai_enhanced_script(model_url, model_name, test_config)
        else:
            k6_script = generator._generate_k6_script(test_config)
        
        return jsonify({
            'k6_script': k6_script,
            'endpoints_count': len(generator._extract_endpoints()),
            'base_url': generator.base_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-swagger', methods=['POST'])
def validate_swagger():
    try:
        data = request.get_json()
        swagger_url = data.get('swagger_url')
        
        if not swagger_url:
            return jsonify({'error': 'Swagger URL is required'}), 400
        
        # Test if we can fetch the Swagger data
        response = requests.get(swagger_url, timeout=10)
        response.raise_for_status()
        
        swagger_data = response.json()
        endpoints = []
        
        if 'paths' in swagger_data:
            for path, methods in swagger_data['paths'].items():
                for method in methods.keys():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        endpoints.append({
                            'path': path,
                            'method': method.upper(),
                            'summary': methods[method].get('summary', '')
                        })
        
        return jsonify({
            'valid': True,
            'endpoints_count': len(endpoints),
            'endpoints': endpoints[:10],  # Return first 10 for preview
            'swagger_info': {
                'title': swagger_data.get('info', {}).get('title', 'Unknown API'),
                'version': swagger_data.get('info', {}).get('version', '1.0.0'),
                'description': swagger_data.get('info', {}).get('description', '')
            }
        })
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'K6 Script Generator'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)