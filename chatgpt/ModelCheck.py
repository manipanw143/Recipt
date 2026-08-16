from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-coder:6.7b"

@app.route("/test-prompt", methods=["POST"])
def test_prompt():
    try:
        data = request.get_json()
        print("📥 Incoming JSON:", data)

        prompt_text = data.get("prompt")
        if not prompt_text:
            return jsonify({"error": "Prompt is required."}), 400

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "stream": False
        }

        print("📤 Sending to Ollama:", payload)
        response = requests.post(OLLAMA_URL, json=payload)
        print("✅ Ollama Raw Response:", response.text)
        response.raise_for_status()
        result = response.json()

        return jsonify({"response": result.get("message", {}).get("content")})

    except requests.exceptions.RequestException as e:
        print("❌ Ollama Error:", str(e))
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print("💥 Server Error:", str(e))
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    try:
        data = request.get_json()
        prompt_text = data.get("prompt")

        if not prompt_text:
            return jsonify({"error": "Prompt is required."}), 400

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        return jsonify({"response": result.get("message", {}).get("content")})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
