from flask import Flask, request, jsonify
import requests
import logging
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:7b"

@app.route('/generate-functional-tests', methods=['POST'])
def generate_test_cases():
    try:
        data = request.json
        swagger_url = data.get("swagger_url")

        if not swagger_url:
            return jsonify({"error": "Swagger URL is required"}), 400

        # Step 1: Fetch Swagger JSON
        swagger_response = requests.get(swagger_url)
        if swagger_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Swagger JSON"}), 500

        swagger_json = swagger_response.text

        # Step 2: Construct prompt
        prompt = f"""
You are a senior QA tester.

Using the Swagger spec below, generate functional test cases in structured JSON format.

Each test case should include:
- feature (from tag or operation summary)
- endpoint
- method
- scenario_title
- type: positive / negative / edge
- request_payload (example input)
- expected_status (from Swagger responses)
- expected_response (based on schema or examples)
- actual_status: null
- actual_response: null
- steps: list of plain English steps

Only output a valid JSON array.

Swagger Spec:
{swagger_json}
"""

        # Step 3: Call Ollama with streaming enabled
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt
        }, stream=True)

        # Step 4: Collect the streamed NDJSON responses
        full_output = ""
        for line in response.iter_lines():
            if line:
                json_data = json.loads(line.decode("utf-8"))
                full_output += json_data.get("response", "")

        return jsonify({"result": full_output.strip()})

    except Exception as e:
        logging.exception("Error generating test cases")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
