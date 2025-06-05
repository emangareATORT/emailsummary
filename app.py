from flask import Flask, request, render_template_string
import openai
import os
import json


def _load_json(content: str):
    """Return dict parsed from the first JSON object found in content."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass
    return None

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-4o-mini-2024-07-18"

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <title>Email Summary</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f7f7f7; }
    .container { background: #fff; padding: 30px 40px; border-radius: 10px; box-shadow: 0 2px 8px #0001; max-width: 800px; margin: 40px auto; }
    textarea, input, select { font-family: inherit; }
    textarea { width: 100%; font-size: 1em; padding: 10px; border-radius: 6px; border: 1px solid #ccc; margin-bottom: 10px; resize: vertical; }
    input[type=submit] { padding: 10px 30px; font-size: 1em; border-radius: 6px; border: none; background: #007bff; color: #fff; cursor: pointer; transition: background 0.2s; }
    input[type=submit]:hover:not(:disabled) { background: #0056b3; }
    input[type=submit]:disabled { background: #aaa; cursor: not-allowed; }
    .error { color: #b30000; background: #ffeaea; padding: 10px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #b30000; }
    .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #155724; }
    h1 { margin-top: 0; }
    label { font-weight: bold; }
    .output { margin-top: 25px; }
    ul { padding-left: 20px; }
    @media (max-width: 600px) {
      .container { padding: 15px 5vw; }
      textarea { font-size: 0.95em; }
    }
    .info { color: #555; font-size: 0.97em; margin-bottom: 10px; }
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
  <div class="info">
    Paste your email chain below and get a summary, people involved, action items, and a reply template.
  </div>
  {% if summary and summary.startswith('Error:') %}
    <div class="error">{{ summary }}</div>
  {% elif summary and summary != "No email chain provided or OPENAI_API_KEY not set" %}
    <div class="success">Summary generated successfully!</div>
  {% elif summary %}
    <div class="error">{{ summary }}</div>
  {% endif %}
  <form method=post autocomplete="off">
    <label for="email_chain">Email Chain</label><br>
    <textarea id="email_chain" name="email_chain" rows=10 placeholder="Paste the full email conversation here..." oninput="checkInput()" required>{{request.form.get('email_chain','')}}</textarea>
    <input id="submitBtn" type=submit value="Summarize">
  </form>
  {% if summary and not summary.startswith('Error:') and summary != "No email chain provided or OPENAI_API_KEY not set" %}
    <div class="output">
      <label for="summary">Summary</label>
      <textarea id="summary" rows="3" readonly>{{summary}}</textarea>
      <label for="people">People Involved</label>
      <ul id="people">
        {% if people %}
          {% if people is string %}
            {% set people_list = people.split(',') %}
          {% else %}
            {% set people_list = people %}
          {% endif %}
          {% for person in people_list %}
            {% if person.strip() %}
              <li>{{ person.strip() }}</li>
            {% endif %}
          {% endfor %}
        {% endif %}
      </ul>
      <label for="actions">Action Items</label>
      <ul id="actions">
        {% if actions %}
          {% if actions is string %}
            {% set actions_list = actions.split('\\n') if '\\n' in actions else actions.split(',') %}
          {% else %}
            {% set actions_list = actions %}
          {% endif %}
          {% for action in actions_list %}
            {% if action.strip() %}
              <li>{{ action.strip() }}</li>
            {% endif %}
          {% endfor %}
        {% endif %}
      </ul>
      <label for="response_template">Response Template</label>
      <textarea id="response_template" rows="5" readonly>{{response_template}}</textarea>
    </div>
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
                "Recibirás una cadena de correos electrónicos. "
                "Responde SOLO en español. "
                "Devuelve un objeto JSON con las siguientes claves: "
                "summary - un resumen breve del hilo; "
                "people - los nombres de todas las personas involucradas; "
                "actions - puntos de acción en viñetas; "
                "response - una posible plantilla de respuesta usando espacios en blanco (_____) para información faltante."
            )
            messages = [
                {"role": "system", "content": "Eres un asistente que resume hilos de correos electrónicos. Responde siempre en español."},
                {"role": "user", "content": f"{prompt}\n\nCadena de correos:\n{email_chain}"}
            ]
            try:
                response = openai.ChatCompletion.create(model=MODEL, messages=messages)
                content = response.choices[0].message.content
                data = _load_json(content)
                if data is not None:
                    summary = data.get("summary")
                    people = data.get("people")
                    actions = data.get("actions")
                    response_template = data.get("response")
                else:
                    summary = "Error: Invalid JSON response from API"
            except Exception as e:
                summary = f"Error: {e}"
        else:
            summary = "No email chain provided or OPENAI_API_KEY not set"
    return render_template_string(TEMPLATE, summary=summary, people=people,
                                  actions=actions, response_template=response_template)

if __name__ == '__main__':
    app.run(debug=True)
