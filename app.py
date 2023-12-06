import json
from flask import Flask, render_template, request, redirect, url_for
import qrcode
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 가상의 메뉴 데이터
menu_items = [
    {"name": "아이스 아메리카노", "price": 3000, "description": "상큼한 아이스 아메리카노", "image": "americano.jpg"},
    {"name": "카페 라떼", "price": 4000, "description": "부드러운 카페 라떼", "image": "latte.jpg"},
    # 추가적인 메뉴 항목을 필요에 따라 추가할 수 있습니다.
]

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_menu_to_file():
    with open('menu_data.json', 'w') as file:
        json.dump(menu_items, file)

def load_menu_from_file():
    try:
        with open('menu_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    return render_template('index.html', menu=menu_items)

@app.route('/menu')
def view_menu():
    return render_template('menu.html', menu=menu_items)

@app.route('/add_menu', methods=['GET', 'POST'])
def add_menu():
    if request.method == 'POST':
        name = request.form['name']
        price = int(request.form['price'])
        description = request.form['description']

        # 파일 업로드 처리
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                flash('이미지 파일이 올바르지 않습니다.', 'error')

        new_menu = {"name": name, "price": price, "description": description, "image": filename}
        menu_items.append(new_menu)

        save_menu_to_file()

        return redirect(url_for('view_menu'))

    return render_template('add_menu.html')

@app.route('/generate_qrcode')
def generate_qrcode():
    # QR 코드에 포함될 URL 생성
    url = request.url_root + 'menu'

    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # QR 코드 이미지 생성
    img = qr.make_image(fill_color="black", back_color="white")

    # 이미지 저장
    img.save('static/images/qrcode.png')

    return render_template('qrcode.html', url=url)

if __name__ == '__main__':
    # 애플리케이션이 실행될 때 저장된 메뉴 데이터를 불러옵니다.
    menu_items = load_menu_from_file()

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
