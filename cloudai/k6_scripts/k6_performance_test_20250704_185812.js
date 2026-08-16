import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCount = new Counter('requests');

// Performance test configuration
export let options = {
    stages: [
        { duration: '2m', target: 10 },    // Ramp up to 10 users
        { duration: '5m', target: 10 },    // Stay at 10 users for 5 minutes
        { duration: '2m', target: 20 },    // Ramp up to 20 users
        { duration: '5m', target: 20 },    // Stay at 20 users for 5 minutes
        { duration: '2m', target: 0 },     // Ramp down to 0 users
    ],
    thresholds: {
        'http_req_duration': ['p(95)<2000'], // 95% of requests should be below 2s
        'errors': ['rate<0.1'],              // Error rate should be below 10%
        'http_req_failed': ['rate<0.1'],     // Failed requests should be below 10%
    },
};

// Base URL
const BASE_URL = 'http://localhost:1339/api';

// Test data
const testData = {
    get/dispensaries: {
        method: 'GET',
        path: '/dispensaries',
        body: null,
        authRequired: false
    },
    post/dispensaries: {
        method: 'POST',
        path: '/dispensaries',
        body: {"data": "test_data"},
        authRequired: false
    },
    get/dispensaries/{id}: {
        method: 'GET',
        path: '/dispensaries/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
    put/dispensaries/{id}: {
        method: 'PUT',
        path: '/dispensaries/test_id',
        body: {"data": "test_data", "id": "test_id"},
        authRequired: false
    },
    delete/dispensaries/{id}: {
        method: 'DELETE',
        path: '/dispensaries/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
    get/hospitals: {
        method: 'GET',
        path: '/hospitals',
        body: null,
        authRequired: false
    },
    post/hospitals: {
        method: 'POST',
        path: '/hospitals',
        body: {"data": "test_data"},
        authRequired: false
    },
    get/hospitals/{id}: {
        method: 'GET',
        path: '/hospitals/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
    put/hospitals/{id}: {
        method: 'PUT',
        path: '/hospitals/test_id',
        body: {"data": "test_data", "id": "test_id"},
        authRequired: false
    },
    delete/hospitals/{id}: {
        method: 'DELETE',
        path: '/hospitals/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
    get/labs: {
        method: 'GET',
        path: '/labs',
        body: null,
        authRequired: false
    },
    post/labs: {
        method: 'POST',
        path: '/labs',
        body: {"data": "test_data"},
        authRequired: false
    },
    get/labs/{id}: {
        method: 'GET',
        path: '/labs/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
    put/labs/{id}: {
        method: 'PUT',
        path: '/labs/test_id',
        body: {"data": "test_data", "id": "test_id"},
        authRequired: false
    },
    delete/labs/{id}: {
        method: 'DELETE',
        path: '/labs/test_id',
        body: {"id": "test_id"},
        authRequired: false
    },
};

// Authentication token (update with actual token)
let authToken = '';

// Helper function to get authorization header
function getAuthHeaders() {
    return authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
}

// Main test function
export default function() {
    // Test each endpoint

    group('get/dispensaries', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = null;
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/dispensaries`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/dispensaries`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/dispensaries failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('post/dispensaries', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data"};
        
        // Make request
        if (payload) {
            response = http.post(`${BASE_URL}/dispensaries`, JSON.stringify(payload), { headers });
        } else {
            response = http.post(`${BASE_URL}/dispensaries`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`post/dispensaries failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('get/dispensaries/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/dispensaries/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/dispensaries/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/dispensaries/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('put/dispensaries/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data", "id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.put(`${BASE_URL}/dispensaries/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.put(`${BASE_URL}/dispensaries/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`put/dispensaries/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('delete/dispensaries/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.delete(`${BASE_URL}/dispensaries/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.delete(`${BASE_URL}/dispensaries/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`delete/dispensaries/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('get/hospitals', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = null;
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/hospitals`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/hospitals`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/hospitals failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('post/hospitals', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data"};
        
        // Make request
        if (payload) {
            response = http.post(`${BASE_URL}/hospitals`, JSON.stringify(payload), { headers });
        } else {
            response = http.post(`${BASE_URL}/hospitals`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`post/hospitals failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('get/hospitals/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/hospitals/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/hospitals/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/hospitals/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('put/hospitals/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data", "id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.put(`${BASE_URL}/hospitals/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.put(`${BASE_URL}/hospitals/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`put/hospitals/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('delete/hospitals/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.delete(`${BASE_URL}/hospitals/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.delete(`${BASE_URL}/hospitals/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`delete/hospitals/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('get/labs', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = null;
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/labs`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/labs`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/labs failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('post/labs', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data"};
        
        // Make request
        if (payload) {
            response = http.post(`${BASE_URL}/labs`, JSON.stringify(payload), { headers });
        } else {
            response = http.post(`${BASE_URL}/labs`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`post/labs failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('get/labs/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.get(`${BASE_URL}/labs/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.get(`${BASE_URL}/labs/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`get/labs/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('put/labs/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"data": "test_data", "id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.put(`${BASE_URL}/labs/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.put(`${BASE_URL}/labs/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`put/labs/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

    group('delete/labs/{id}', function() {
        let headers = {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        };
        
        let response;
        let payload = {"id": "test_id"};
        
        // Make request
        if (payload) {
            response = http.delete(`${BASE_URL}/labs/test_id`, JSON.stringify(payload), { headers });
        } else {
            response = http.delete(`${BASE_URL}/labs/test_id`, { headers });
        }
        
        // Record metrics
        requestCount.add(1);
        responseTime.add(response.timings.duration);
        
        // Check response
        let success = check(response, {
            'status is 2xx': (r) => r.status >= 200 && r.status < 300,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
            'response has body': (r) => r.body.length > 0,
        });
        
        if (!success) {
            errorRate.add(1);
            console.error(`delete/labs/{id} failed: ${response.status} - ${response.body}`);
        }
        
        // Think time between requests
        sleep(1);
    });

}

// Setup function - runs once before the test
export function setup() {
    console.log('Starting performance test...');
    
    // TODO: Add authentication setup if needed
    // authToken = getAuthToken();
    
    return { timestamp: Date.now() };
}

// Teardown function - runs once after the test
export function teardown(data) {
    console.log(`Performance test completed at ${new Date(data.timestamp)}`);
}

// Helper functions
function getAuthToken() {
    // TODO: Implement authentication logic
    // Example:
    // let loginResponse = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    //     username: 'testuser',
    //     password: 'testpass'
    // }), { headers: { 'Content-Type': 'application/json' } });
    // 
    // return JSON.parse(loginResponse.body).token;
    return '';
}
