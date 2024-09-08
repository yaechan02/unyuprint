from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 업로드 폴더 경로 설정
UPLOAD_FOLDER = 'uploads'  # 파일을 저장할 폴더
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'hwp', 'hwpx', 'doc', 'docx'}  # 허용된 파일 확장자

# JSON 파일 경로 설정
JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selected_dates.json')

# 업로드 폴더가 없으면 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 허용된 파일 확장자를 확인하는 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 홈 페이지 (기본 일정 예약 페이지)
@app.route("/")
def home():
    return render_template("index.html")

# JSON 파일 데이터를 반환하는 API 엔드포인트
@app.route("/api/get_data", methods=["GET"])
def get_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            return jsonify(data)
    else:
        return jsonify([])

# 파일 열람 (다운로드) 엔드포인트
@app.route('/uploads/<filename>', methods=['GET'])
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 데이터를 삭제하는 API 엔드포인트
@app.route("/api/delete/<int:index>", methods=["DELETE"])
def delete_entry(index):
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # 인덱스에 해당하는 항목 삭제
        if 0 <= index < len(data):
            entry = data.pop(index)
            
            # 파일이 있으면 파일도 삭제
            if "uploadedFile" in entry and entry["uploadedFile"]:
                file_path = os.path.join(UPLOAD_FOLDER, entry["uploadedFile"])
                if os.path.exists(file_path):
                    os.remove(file_path)

            # JSON 파일 업데이트
            with open(JSON_FILE, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Data not found"}), 404

# 예약된 시간을 반환하는 API 엔드포인트 추가
@app.route("/get_reserved_times", methods=["GET"])
def get_reserved_times():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            # 예약된 시간 목록을 추출
            reserved_times = [entry['time'] for entry in data if 'time' in entry]
            return jsonify({"reservedTimes": reserved_times})
    return jsonify({"reservedTimes": []})

# 데이터 저장 (예약 및 파일 업로드)
@app.route("/save_time", methods=["POST"])
def save_time():
    time = request.form.get("time")
    description = request.form.get("description")
    upload_method = request.form.get("uploadMethod")  # 업로드 방식

    uploaded_file_name = None  # 파일 이름을 저장할 변수

    # 파일이 업로드되었는지 확인
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # 파일 이름을 안전하게 변경
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # 파일 저장
            uploaded_file_name = filename  # 저장된 파일 이름 기록

    # 기존 데이터를 불러오기 (기존 파일이 있으면 읽어오고 없으면 빈 리스트)
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as json_file:
            try:
                existing_data = json.load(json_file)
            except (json.JSONDecodeError, ValueError):
                existing_data = []  # 파일이 비어있거나 JSON 오류 발생 시 초기화
    else:
        existing_data = []

    # 새 데이터를 배열에 추가
    new_entry = {
        "time": time,
        "description": description,
        "uploadMethod": upload_method,
        "uploadedFile": uploaded_file_name  # 저장된 파일 이름 기록
    }
    existing_data.append(new_entry)  # 기존 데이터에 새 데이터를 추가

    # 데이터를 JSON 파일로 저장 (덮어쓰지 않고 추가된 데이터 포함)
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, ensure_ascii=False, indent=4)
        print("데이터가 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        return jsonify({"status": "error", "message": str(e)})

    return jsonify({"status": "success"})

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  # 업로드 폴더가 없으면 생성
    app.run(debug=True)
