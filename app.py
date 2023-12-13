import json
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

class MenuItem:
    def __init__(self, name, description, price, image_filename):
        self.name = name
        self.description = description
        self.price = price
        self.image_filename = image_filename

# JSON 파일 경로
orders_file_path = 'orders.json'
menu_file_path = 'menu.json'

# 메뉴 초기 데이터 로드
def load_menu():
    try:
        with open(menu_file_path, 'r', encoding='utf-8') as file:
            menu_items = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        menu_items = []
    return [MenuItem(**item) for item in menu_items]

# 주문 내역 초기 데이터 로드
def load_orders():
    try:
        with open(orders_file_path, 'r', encoding='utf-8') as file:
            orders = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        orders = []
    return orders

menu_items = load_menu()
all_orders = load_orders()

@app.route('/')
def home():
    return render_template('index.html', menu_items=menu_items)

@app.route('/menu/<table_number>', methods=['GET', 'POST'])
def menu(table_number):
    if request.method == 'POST':
        # 주문 로직 처리
        order_data = request.form.get('order_data')

        # 주문 내역 저장
        all_orders.append({'table_number': table_number, 'order_data': order_data})

        # 주문 내역을 JSON 파일에 저장
        with open('orders.json', 'w') as file:
            json.dump(all_orders, file)

        # 실시간으로 주문 내역을 클라이언트에게 알림
        socketio.emit('order_update', {'table_number': table_number, 'order_data': order_data}, namespace='/orders')

    # 메뉴 데이터를 템플릿으로 전달
    return render_template('menu.html', table_number=table_number, menu_items=menu_items)


# 주문 내역 페이지
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    return render_template('orders.html', all_orders=all_orders)

# 주문 내역 삭제
@app.route('/delete_order/<table_number>', methods=['POST'])
def delete_order(table_number):
    # Delete orders associated with the table
    all_orders[:] = [order for order in all_orders if order['table_number'] != table_number]

    # Notify clients about the order deletion
    socketio.emit('order_delete', {'table_number': table_number}, namespace='/orders')

    return redirect(url_for('orders'))

# WebSocket 네임스페이스
@socketio.on('connect', namespace='/orders')
def handle_connect():
    print('Client connected to orders namespace')

@app.route('/menu_update', methods=['GET', 'POST'])
def menu_update():
    if request.method == 'POST':
        # 새로운 메뉴 항목 추가
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))

        # 이미지 파일 저장
        image_file = request.files['image']
        image_filename = image_file.filename if image_file else None
        if image_filename:
            image_path = os.path.join('static', 'images', image_filename)
            image_file.save(image_path)

        new_item = MenuItem(name, description, price, image_filename)
        menu_items.append(new_item)

        # 메뉴 항목을 JSON 파일에 저장
        save_menu()

        # 리디렉션을 통해 새로고침 시 "페이지 없음" 오류 방지
        return redirect(url_for('menu_update'))

    return render_template('menu_update.html', menu_items=menu_items)

# JSON 파일에 주문 내역 저장
def save_orders():
    with open(orders_file_path, 'w') as file:
        json.dump(all_orders, file)

# JSON 파일에 메뉴 저장
def save_menu():
    menu_data = [{'name': item.name, 'description': item.description, 'price': item.price, 'image_filename': item.image_filename} for item in menu_items]
    with open(menu_file_path, 'w') as file:
        json.dump(menu_data, file)

@app.route('/delete_menu_item/<int:index>', methods=['DELETE'])
def delete_menu_item(index):
    if 0 <= index < len(menu_items):
        del menu_items[index]
        # 메뉴 항목을 JSON 파일에 저장
        save_menu()
        return 'Menu item deleted successfully', 200
    return 'Invalid index', 404

@app.route('/qrcode')
def qrcode():
    return render_template('qrcode.html')

if __name__ == '__main__':
    # 애플리케이션 실행
    socketio.run(app, debug=True)
