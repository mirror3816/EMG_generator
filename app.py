import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import qrcode
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 비밀키를 안전한 방법으로 설정하세요.

# 가상의 사용자 데이터
users = {}

USERS_FILE = 'users.json'

def save_users_to_file(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file)

def load_users_from_file():
    try:
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# 가상의 메뉴 데이터
menu_items = []

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
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    users = load_users_from_file()

    if not users:
        # 최초 로그인 시 회원가입 처리
        users[username] = password
        save_users_to_file(users)

        session['username'] = username
        flash('처음 로그인하여 회원 가입이 완료되었습니다.', 'success')
        return redirect(url_for('menu'))
    elif username in users and users[username] == password:
        session['username'] = username
        flash('로그인 성공!', 'success')
        return redirect(url_for('menu'))
    else:
        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
        return redirect(url_for('index'))

@app.route('/menu')
def menu():
    if 'username' in session:
        return render_template('menu.html', menu=menu_items)
    else:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

@app.route('/add_menu', methods=['GET', 'POST'])
def add_menu():
    if 'username' in session:
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

            return redirect(url_for('menu'))

        return render_template('add_menu.html')
    else:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

@app.route('/generate_qrcode')
def generate_qrcode():
    if 'username' in session:
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
    else:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

@app.route('/delete_menu/<int:menu_index>', methods=['GET', 'POST'])
def delete_menu(menu_index):
    if 'username' in session:
        if request.method == 'POST':
            del menu_items[menu_index]
            save_menu_to_file()
            return redirect(url_for('menu'))

        return render_template('delete_menu.html', menu_index=menu_index, menu_item=menu_items[menu_index])
    else:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 애플리케이션이 실행될 때 저장된 메뉴 데이터를 불러옵니다.
    menu_items = load_menu_from_file()

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
