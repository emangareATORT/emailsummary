from flask import Flask, request, render_template_string
import openai
import os
import json

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-4o-mini-2024-07-18"

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <title>Email Summary</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; background: #f7f7f7; }
    .container { background: #fff; padding: 30px 40px; border-radius: 10px; box-shadow: 0 2px 8px #0001; max-width: 800px; margin: auto; }
    textarea { width: 100%; font-size: 1em; padding: 10px; border-radius: 6px; border: 1px solid #ccc; }
    input[type=submit] { padding: 10px 30px; font-size: 1em; border-radius: 6px; border: none; background: #007bff; color: #fff; cursor: pointer; }
    input[type=submit]:disabled { background: #aaa; cursor: not-allowed; }
    .error { color: #b30000; background: #ffeaea; padding: 10px; border-radius: 6px; margin-bottom: 15px; }
    .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 6px; margin-bottom: 15px; }
    h1 { margin-top: 0; }
    pre { background: #f4f4f4; padding: 10px; border-radius: 6px; }
    label { font-weight: bold; }
  </style>
  <script>
    function checkInput() {
      var ta = document.getElementById('email_chain');
      document.getElementById('submitBtn').disabled = ta.value.trim().length === 0;
    }
    window.onload = checkInput;
  </script>
</head>
<body>
<div class="container">
  <h1>Email Chain Summarizer</h1>
  {% if summary and summary.startswith('Error:') %}
    <div class="error">{{ summary }}</div>
  {% elif summary and summary != "No email chain provided or OPENAI_API_KEY not set" %}
    <div class="success">Summary generated successfully!</div>
  {% elif summary %}
    <div class="error">{{ summary }}</div>
  {% endif %}
  <form method=post>
    <label for="email_chain">Paste your email chain below:</label><br>
    <textarea id="email_chain" name="email_chain" rows=12 placeholder="Paste the full email conversation here..." oninput="checkInput()">{{request.form.get('email_chain','')}}</textarea><br>
    <input id="submitBtn" type=submit value="Summarize">
  </form>
  {% if summary and not summary.startswith('Error:') and summary != "No email chain provided or OPENAI_API_KEY not set" %}
    <h2>Summary</h2>
    <pre>{{summary}}</pre>
    <h2>People Involved</h2>
    <pre>{{people}}</pre>
    <h2>Action Items</h2>
    <pre>{{actions}}</pre>
    <h2>Response Template</h2>
    <pre>{{response_template}}</pre>
  {% endif %}
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = people = actions = response_template = None
    if request.method == 'POST':
        email_chain = request.form.get('email_chain', '')
        if email_chain and openai.api_key:
            prompt = (
                "You will receive a chain of emails. "
                "Provide a JSON object with the following keys:"
                " summary - a short summary of the thread;"
                " people - the names of all people involved;"
                " actions - bullet points of action items;"
                " response - a possible reply template using blanks (_____) for missing info."
            )
            messages = [
                {"role": "system", "content": "You are an assistant that summarizes email threads."},
                {"role": "user", "content": f"{prompt}\n\nEmail chain:\n{email_chain}"}
            ]
            try:
                response = openai.ChatCompletion.create(model=MODEL, messages=messages)
                content = response.choices[0].message.content
                try:
                    data = json.loads(content)
                    summary = data.get("summary")
                    people = data.get("people")
                    actions = data.get("actions")
                    response_template = data.get("response")
                except json.JSONDecodeError:
                    summary = content
            except Exception as e:
                summary = f"Error: {e}"
        else:
            summary = "No email chain provided or OPENAI_API_KEY not set"
    return render_template_string(TEMPLATE, summary=summary, people=people,
                                  actions=actions, response_template=response_template)

if __name__ == '__main__':
    app.run(debug=True)
