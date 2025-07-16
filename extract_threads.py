import os
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/extract_threads', methods=['POST'])
def extract_threads():
    data = request.get_json()

    json_path = data.get('json_path')
    output_dir = data.get('output_dir', '/Users/yokota/Desktop/gpt/logs/')

    if not json_path or not os.path.isfile(json_path):
        return jsonify({'error': f"ファイル '{json_path}' が見つかりません。"}), 400

    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    titles = [conv.get('title', 'untitled') for conv in conversations]

    for idx, conv in enumerate(conversations):
        title = titles[idx]
        safe_title = ''.join(c if c not in '/:*?"<>|' else '_' for c in title)
        if len(safe_title) < 3:
            safe_title = f"thread_{idx}_{safe_title}"

        output_file = os.path.join(output_dir, f"{idx}_{safe_title}.txt")

        header = (
            f"# 作成日: {datetime.today().strftime('%Y-%m-%d')}\n"
            f"# 会話スレッド: {title}\n"
            f"# 抽出日時: {datetime.now()}\n"
            f"# 抽出元: {json_path}\n\n"
        )

        with open(output_file, 'w', encoding='utf-8') as out:
            out.write(header)

            messages = conv.get('mapping', {})
            for node in messages.values():
                msg = node.get('message')
                if not msg:
                    continue

                content = msg.get('content', {})
                parts = content.get('parts', [])
                if not parts or not parts[0] or content.get('content_type') != 'text':
                    continue

                role = msg.get('author', {}).get('role', 'unknown')
                time = msg.get('create_time')
                prefix = 'User: ' if role == 'user' else 'Assistant: '

                if time:
                    timestamp = datetime.fromtimestamp(time).isoformat()
                    out.write(f"[{timestamp}] {prefix}\"{parts[0]}\"\n")
                else:
                    out.write(f"{prefix}\"{parts[0]}\"\n")

    return jsonify({'message': f"{len(titles)} 個のスレッドを {output_dir} に抽出しました。"})

if __name__ == '__main__':
    app.run(debug=True)
