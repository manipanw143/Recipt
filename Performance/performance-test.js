import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time', true);
const requestCounter = new Counter('requests_total');

// Test configuration
export const options = {
    vus: 10,
    duration: '30s',
    stages: [
        { duration: '10s', target: 10 },
        { duration: '30s', target: 10 },
        { duration: '10s', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000', 'p(99)<5000'],
        http_req_failed: ['rate<0.1'],
        error_rate: ['rate<0.1'],
        checks: ['rate>0.9'],
    },
};

// Helper functions
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
}

// Test data
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
}

// Setup function - runs once before all VUs
export function setup() {
    console.log('Starting performance test...');
    console.log(`Test will run with ${__ENV.K6_VUS || options.vus} virtual users`);
    
    // You can perform authentication or data setup here
    return {
        authToken: __ENV.AUTH_TOKEN || 'default_token',
        baseUrl: __ENV.BASE_URL || '',
    };
}

// Main test function
export default function(data) {
    const baseUrl = data?.baseUrl || 'http://localhost:1339/api';
    const headers = getAuthHeaders();
    
    group('API Performance Test', () => {
        // Test critical user journeys
        group('User Journey 1 - Basic Operations', () => {
            test_get_dispensaries(baseUrl, headers);
            test_post_dispensaries(baseUrl, headers);
            test_get_dispensaries_id(baseUrl, headers);
            test_put_dispensaries_id(baseUrl, headers);
            test_delete_dispensaries_id(baseUrl, headers);
            test_get_hospitals(baseUrl, headers);
            test_post_hospitals(baseUrl, headers);
            test_get_hospitals_id(baseUrl, headers);
            test_put_hospitals_id(baseUrl, headers);
            test_delete_hospitals_id(baseUrl, headers);
        });
        
        // Add more test groups as needed
        group('Load Test - Random Endpoints', () => {
            const endpoints = ["/dispensaries", "/dispensaries", "/dispensaries/{id}", "/dispensaries/{id}", "/dispensaries/{id}"];
            const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
            
            const response = http.get(`${baseUrl}${randomEndpoint}`, { headers });
            validateResponse(response);
        });
    });
    
    // Random sleep between 1-3 seconds to simulate user behavior
    sleep(randomIntBetween(1, 3));
}

function test_get_dispensaries(baseUrl, headers) {
    const url = `${baseUrl}/dispensaries`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /dispensaries');
    
    if (!isValid) {
        console.warn(`Failed request to /dispensaries`);
    }
    
    return response;
}

function test_post_dispensaries(baseUrl, headers) {
    const url = `${baseUrl}/dispensaries`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /dispensaries');
    
    if (!isValid) {
        console.warn(`Failed request to /dispensaries`);
    }
    
    return response;
}

function test_get_dispensaries_id(baseUrl, headers) {
    const url = `${baseUrl}/dispensaries/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /dispensaries/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /dispensaries/{id}`);
    }
    
    return response;
}

function test_put_dispensaries_id(baseUrl, headers) {
    const url = `${baseUrl}/dispensaries/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /dispensaries/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /dispensaries/{id}`);
    }
    
    return response;
}

function test_delete_dispensaries_id(baseUrl, headers) {
    const url = `${baseUrl}/dispensaries/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /dispensaries/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /dispensaries/{id}`);
    }
    
    return response;
}

function test_get_hospitals(baseUrl, headers) {
    const url = `${baseUrl}/hospitals`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /hospitals');
    
    if (!isValid) {
        console.warn(`Failed request to /hospitals`);
    }
    
    return response;
}

function test_post_hospitals(baseUrl, headers) {
    const url = `${baseUrl}/hospitals`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /hospitals');
    
    if (!isValid) {
        console.warn(`Failed request to /hospitals`);
    }
    
    return response;
}

function test_get_hospitals_id(baseUrl, headers) {
    const url = `${baseUrl}/hospitals/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /hospitals/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /hospitals/{id}`);
    }
    
    return response;
}

function test_put_hospitals_id(baseUrl, headers) {
    const url = `${baseUrl}/hospitals/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /hospitals/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /hospitals/{id}`);
    }
    
    return response;
}

function test_delete_hospitals_id(baseUrl, headers) {
    const url = `${baseUrl}/hospitals/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /hospitals/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /hospitals/{id}`);
    }
    
    return response;
}

function test_get_labs(baseUrl, headers) {
    const url = `${baseUrl}/labs`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /labs');
    
    if (!isValid) {
        console.warn(`Failed request to /labs`);
    }
    
    return response;
}

function test_post_labs(baseUrl, headers) {
    const url = `${baseUrl}/labs`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /labs');
    
    if (!isValid) {
        console.warn(`Failed request to /labs`);
    }
    
    return response;
}

function test_get_labs_id(baseUrl, headers) {
    const url = `${baseUrl}/labs/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /labs/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /labs/{id}`);
    }
    
    return response;
}

function test_put_labs_id(baseUrl, headers) {
    const url = `${baseUrl}/labs/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /labs/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /labs/{id}`);
    }
    
    return response;
}

function test_delete_labs_id(baseUrl, headers) {
    const url = `${baseUrl}/labs/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /labs/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /labs/{id}`);
    }
    
    return response;
}

function test_get_prescriptions(baseUrl, headers) {
    const url = `${baseUrl}/prescriptions`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /prescriptions');
    
    if (!isValid) {
        console.warn(`Failed request to /prescriptions`);
    }
    
    return response;
}

function test_post_prescriptions(baseUrl, headers) {
    const url = `${baseUrl}/prescriptions`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /prescriptions');
    
    if (!isValid) {
        console.warn(`Failed request to /prescriptions`);
    }
    
    return response;
}

function test_get_prescriptions_id(baseUrl, headers) {
    const url = `${baseUrl}/prescriptions/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /prescriptions/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /prescriptions/{id}`);
    }
    
    return response;
}

function test_put_prescriptions_id(baseUrl, headers) {
    const url = `${baseUrl}/prescriptions/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /prescriptions/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /prescriptions/{id}`);
    }
    
    return response;
}

function test_delete_prescriptions_id(baseUrl, headers) {
    const url = `${baseUrl}/prescriptions/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /prescriptions/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /prescriptions/{id}`);
    }
    
    return response;
}

function test_post_upload(baseUrl, headers) {
    const url = `${baseUrl}/upload`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /upload');
    
    if (!isValid) {
        console.warn(`Failed request to /upload`);
    }
    
    return response;
}

function test_post_upload_id_id(baseUrl, headers) {
    const url = `${baseUrl}/upload?id=${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /upload?id={id}');
    
    if (!isValid) {
        console.warn(`Failed request to /upload?id={id}`);
    }
    
    return response;
}

function test_get_upload_files(baseUrl, headers) {
    const url = `${baseUrl}/upload/files`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /upload/files');
    
    if (!isValid) {
        console.warn(`Failed request to /upload/files`);
    }
    
    return response;
}

function test_get_upload_files_id(baseUrl, headers) {
    const url = `${baseUrl}/upload/files/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /upload/files/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /upload/files/{id}`);
    }
    
    return response;
}

function test_delete_upload_files_id(baseUrl, headers) {
    const url = `${baseUrl}/upload/files/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /upload/files/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /upload/files/{id}`);
    }
    
    return response;
}

function test_get_connect_provider(baseUrl, headers) {
    const url = `${baseUrl}/connect/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /connect/{provider}');
    
    if (!isValid) {
        console.warn(`Failed request to /connect/{provider}`);
    }
    
    return response;
}

function test_post_auth_local(baseUrl, headers) {
    const url = `${baseUrl}/auth/local`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/local');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/local`);
    }
    
    return response;
}

function test_post_auth_local_register(baseUrl, headers) {
    const url = `${baseUrl}/auth/local/register`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/local/register');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/local/register`);
    }
    
    return response;
}

function test_get_auth_provider_callback(baseUrl, headers) {
    const url = `${baseUrl}/auth/${randomIntBetween(1, 100)}/callback`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /auth/{provider}/callback');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/{provider}/callback`);
    }
    
    return response;
}

function test_post_auth_forgot_password(baseUrl, headers) {
    const url = `${baseUrl}/auth/forgot-password`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/forgot-password');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/forgot-password`);
    }
    
    return response;
}

function test_post_auth_reset_password(baseUrl, headers) {
    const url = `${baseUrl}/auth/reset-password`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/reset-password');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/reset-password`);
    }
    
    return response;
}

function test_post_auth_change_password(baseUrl, headers) {
    const url = `${baseUrl}/auth/change-password`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/change-password');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/change-password`);
    }
    
    return response;
}

function test_get_auth_email_confirmation(baseUrl, headers) {
    const url = `${baseUrl}/auth/email-confirmation`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /auth/email-confirmation');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/email-confirmation`);
    }
    
    return response;
}

function test_post_auth_send_email_confirmation(baseUrl, headers) {
    const url = `${baseUrl}/auth/send-email-confirmation`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /auth/send-email-confirmation');
    
    if (!isValid) {
        console.warn(`Failed request to /auth/send-email-confirmation`);
    }
    
    return response;
}

function test_get_users_permissions_permissions(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/permissions`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users-permissions/permissions');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/permissions`);
    }
    
    return response;
}

function test_get_users_permissions_roles(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/roles`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users-permissions/roles');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/roles`);
    }
    
    return response;
}

function test_post_users_permissions_roles(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/roles`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /users-permissions/roles');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/roles`);
    }
    
    return response;
}

function test_get_users_permissions_roles_id(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/roles/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users-permissions/roles/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/roles/{id}`);
    }
    
    return response;
}

function test_put_users_permissions_roles_role(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/roles/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /users-permissions/roles/{role}');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/roles/{role}`);
    }
    
    return response;
}

function test_delete_users_permissions_roles_role(baseUrl, headers) {
    const url = `${baseUrl}/users-permissions/roles/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /users-permissions/roles/{role}');
    
    if (!isValid) {
        console.warn(`Failed request to /users-permissions/roles/{role}`);
    }
    
    return response;
}

function test_get_users(baseUrl, headers) {
    const url = `${baseUrl}/users`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users');
    
    if (!isValid) {
        console.warn(`Failed request to /users`);
    }
    
    return response;
}

function test_post_users(baseUrl, headers) {
    const url = `${baseUrl}/users`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.post(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'POST /users');
    
    if (!isValid) {
        console.warn(`Failed request to /users`);
    }
    
    return response;
}

function test_get_users_id(baseUrl, headers) {
    const url = `${baseUrl}/users/${randomIntBetween(1, 100)}`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /users/{id}`);
    }
    
    return response;
}

function test_put_users_id(baseUrl, headers) {
    const url = `${baseUrl}/users/${randomIntBetween(1, 100)}`;
        const payload = generateRandomPayload({
            // Add specific fields based on your API schema
        });
        const body = JSON.stringify(payload);
    
    const response = http.put(url, { headers, body });
    
    const isValid = validateResponse(response);
    logResponse(response, 'PUT /users/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /users/{id}`);
    }
    
    return response;
}

function test_delete_users_id(baseUrl, headers) {
    const url = `${baseUrl}/users/${randomIntBetween(1, 100)}`;
    
    const response = http.delete(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'DELETE /users/{id}');
    
    if (!isValid) {
        console.warn(`Failed request to /users/{id}`);
    }
    
    return response;
}

function test_get_users_me(baseUrl, headers) {
    const url = `${baseUrl}/users/me`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users/me');
    
    if (!isValid) {
        console.warn(`Failed request to /users/me`);
    }
    
    return response;
}

function test_get_users_count(baseUrl, headers) {
    const url = `${baseUrl}/users/count`;
    
    const response = http.get(url, { headers });
    
    const isValid = validateResponse(response);
    logResponse(response, 'GET /users/count');
    
    if (!isValid) {
        console.warn(`Failed request to /users/count`);
    }
    
    return response;
}

// Teardown function - runs once after all VUs complete
export function teardown(data) {
    console.log('Performance test completed!');
    console.log('Check the results for detailed metrics.');
    
    // Cleanup operations can be performed here
}