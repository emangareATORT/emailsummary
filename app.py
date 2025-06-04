from flask import Flask, request, render_template_string
import openai
import os
import json

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-4o"

TEMPLATE = """
<!doctype html>
<title>Email Summary</title>
<h1>Email Chain Summarizer</h1>
<form method=post>
  <textarea name=email_chain rows=20 cols=100 placeholder="Paste email chain here">{{request.form.get('email_chain','')}}</textarea><br>
  <input type=submit value="Summarize">
</form>
{% if summary %}
<h2>Summary</h2>
<pre>{{summary}}</pre>
<h2>People Involved</h2>
<pre>{{people}}</pre>
<h2>Action Items</h2>
<pre>{{actions}}</pre>
<h2>Response Template</h2>
<pre>{{response_template}}</pre>
{% endif %}
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = people = actions = response_template = None
    if request.method == 'POST':
        email_chain = request.form.get('email_chain', '')
        if email_chain and openai.api_key:
            prompt = (
                "You will receive a chain of emails. "
                "Provide a JSON object with the following keys:"\
                " summary - a short summary of the thread;"\
                " people - the names of all people involved;"\
                " actions - bullet points of action items;"\
                " response - a possible reply template using blanks (_____) for missing info."\
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
