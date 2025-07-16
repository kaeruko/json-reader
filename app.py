from flask import Flask, request, render_template_string, send_file
from datetime import datetime
import json
import io

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<title>スレッド抽出ツール</title>
<h1>JSONファイルをアップロードしてスレッドをまとめて抽出</h1>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".json" required>
    <input type="submit" value="抽出してダウンロード">
</form>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if not uploaded_file:
            return "ファイルが見つかりませんでした", 400

        try:
            conversations = json.load(uploaded_file)
            output = io.StringIO()

            for idx, conv in enumerate(conversations):
                title = conv.get("title", f"untitled_{idx}")
                safe_title = ''.join(c if c not in '/:*?"<>|' else '_' for c in title)
                if len(safe_title) < 3:
                    safe_title = f"thread_{idx}_{safe_title}"

                header = (
                    f"# 作成日: {datetime.today().strftime('%Y-%m-%d')}\n"
                    f"# 会話スレッド: {title}\n"
                    f"# 抽出日時: {datetime.now()}\n\n"
                )
                output.write(header)

                messages = conv.get("mapping", {})
                for node in messages.values():
                    msg = node.get("message")
                    if not msg:
                        continue

                    content = msg.get("content", {})
                    parts = content.get("parts", [])
                    if not parts or not parts[0] or content.get("content_type") != "text":
                        continue

                    role = msg.get("author", {}).get("role", "unknown")
                    prefix = "User: " if role == "user" else "Assistant: "
                    time = msg.get("create_time")
                    if time:
                        timestamp = datetime.fromtimestamp(time).isoformat()
                        output.write(f"[{timestamp}] {prefix}\"{parts[0]}\"\n")
                    else:
                        output.write(f"{prefix}\"{parts[0]}\"\n")

                output.write("\n" + "="*40 + "\n\n")

            # まとめた内容をファイルとして返す
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/plain",
                as_attachment=True,
                download_name="extracted_threads.txt"
            )

        except Exception as e:
            return f"エラーが発生しました: {str(e)}", 500

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
