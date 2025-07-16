from flask import Flask, request, render_template_string
from datetime import datetime
import json
import io
import html

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<title>ChatGPTのログを表示する</title>
<h1>conversations.jsonをアップロード</h1>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".json" required>
    <input type="submit" value="表示">
</form>

{% if threads %}
  <hr>
  <h2>抽出されたスレッド:</h2>
  {% for thread in threads %}
    <div style="border:1px solid #ccc; padding:10px; margin-bottom:20px;">
      <h3>{{ thread.title }}</h3>
      <pre style="white-space: pre-wrap; font-family: monospace;">{{ thread.content }}</pre>
    </div>
  {% endfor %}
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    threads = []
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if not uploaded_file:
            return "ファイルが見つかりませんでした", 400

        try:
            conversations = json.load(uploaded_file)

            for idx, conv in enumerate(conversations):
                title = conv.get("title", f"untitled_{idx}")
                messages = conv.get("mapping", {})
                thread_text = ""

                for node in messages.values():
                    msg = node.get("message")
                    if not msg:
                        continue

                    content = msg.get("content", {})
                    parts = content.get("parts", [])
                    if not parts or not parts[0] or content.get("content_type") != "text":
                        continue

                    role = msg.get("author", {}).get("role", "unknown")
                    prefix = "**User**: " if role == "user" else "**Assistant**: "
                    time = msg.get("create_time")
                    if time:
                        timestamp = datetime.fromtimestamp(time).isoformat()
                        thread_text += f"- [{timestamp}] {prefix}{parts[0]}\n"
                    else:
                        thread_text += f"- {prefix}{parts[0]}\n"

                threads.append({
                    "title": html.escape(title),
                    "content": html.escape(thread_text)
                })

        except Exception as e:
            threads = [{"title": "エラー", "content": str(e)}]

    return render_template_string(HTML_TEMPLATE, threads=threads)

if __name__ == "__main__":
    app.run(debug=True)
