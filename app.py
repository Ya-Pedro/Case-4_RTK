from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from services import get_user_by_login, get_user_requests, get_all_requests
from dotenv import load_dotenv
import os
from datetime import date, datetime, timedelta
from models import VacationBalance, VacationRequest
from sqlalchemy.orm import Session
from services import SessionLocal, get_user_by_id
from services import get_user_by_id, get_departments_dict, get_all_requests
from flask import request, flash
import csv
import io

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route('/logout')
def logout():
    session.clear()  # удаляем все данные сессии
    return redirect(url_for('login'))  # перенаправляем на страницу логина

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    return login() 

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')  # безопаснее
        password = request.form.get('password')
        if not login or not password:
            return render_template('login.html', error="Введите логин и пароль")
        user = get_user_by_login(login)
        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'employee':
                return redirect(url_for('employee_dashboard'))
            elif user.role == 'manager':
                return redirect(url_for('manager_dashboard'))
            elif user.role == 'hr':
                return redirect(url_for('hr_dashboard'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")
    return render_template('login.html')

def get_home_url():
    role = session.get('role')
    if role == 'employee':
        return url_for('employee_dashboard')
    elif role == 'manager':
        return url_for('manager_dashboard')
    elif role == 'hr':
        return url_for('hr_dashboard')
    return url_for('login')

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    current_user = get_user_by_id(user_id) if user_id else None
    return {'current_user': current_user, 'home_url': get_home_url()}

@app.route('/manager/action', methods=['POST'])
def manager_action():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    req_id = request.form.get('id')
    action = request.form.get('action')
    comment = request.form.get('comment', '')

    session_db = SessionLocal()
    req = session_db.query(VacationRequest).filter_by(id=req_id).first()
    if not req:
        session_db.close()
        return "Заявка не найдена", 404

    if action == 'approve':
        req.status = 'approved'
    elif action == 'reject':
        req.status = 'rejected'
        req.comment = comment

    session_db.commit()
    session_db.close()

    return redirect(url_for('manager_dashboard'))

# Дашборды
@app.route('/request/new', methods=['GET', 'POST'])
def create_request():
    if session.get('role') != 'employee':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    if request.method == 'POST':
        from uuid import uuid4
        new_req = VacationRequest(
            id=str(uuid4()),
            user_id=user_id,
            start_date=request.form['start_date'],
            end_date=request.form['end_date'],
            type=request.form['type'],
            status='pending',
            comment=request.form.get('comment', ''),
            created_at=date.today()
        )
        session_db = SessionLocal()
        session_db.add(new_req)
        session_db.commit()
        session_db.close()
        return redirect(url_for('employee_dashboard'))
    
    return render_template('request_create.html')



# --- Employee: личные заявки ---
@app.route('/employee')
def employee_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    current_year = date.today().year
    session_db = SessionLocal()

    # Баланс отпуска
    bal = session_db.query(VacationBalance).filter_by(user_id=user_id, year=current_year).first()
    if not bal:
        class EmptyBalance:
            total_days = 0
            used_days = 0
        bal = EmptyBalance()

    # Запланированные отпуска
    requests = get_user_requests(user_id)
    planned = sum(
        (r.end_date - r.start_date).days + 1
        for r in requests
        if r.status in ('pending', 'approved') and r.start_date >= date.today()
    )
    available = bal.total_days - bal.used_days - planned
    session_db.close()

    return render_template('employee_dashboard.html',
                           requests=requests,
                           bal=bal,
                           planned=planned,
                           available=available,
                           current_year=current_year)

@app.route('/hr/requests')
def hr_requests():
    if session.get('role') != 'hr':
        return redirect(url_for('login'))
    requests = get_all_requests()
    departments = get_departments_dict()
    return render_template('hr_requests.html', requests=requests, departments=departments, services={'get_user_by_id': get_user_by_id})

@app.route('/api/events')
def api_events():
    if 'user_id' not in session:
        return jsonify([])  # если не залогинен

    user_role = session.get('role')
    events = []

    # Получаем все заявки
    all_requests = get_all_requests()  # или фильтруем по отделу для менеджера/HR

    for r in all_requests:
        # Цвет в зависимости от статуса
        if r.status == 'approved':
            color = 'green'
            title_status = 'Согласовано'
        elif r.status == 'pending':
            color = 'yellow'
            title_status = 'На рассмотрении'
        else:
            color = 'red'
            title_status = 'Отклонено'

        events.append({
            'title': f"{get_user_by_id(r.user_id).full_name} ({title_status})",
            'start': r.start_date.isoformat(),
            'end': (r.end_date + timedelta(days=1)).isoformat(),  # FullCalendar включает end день как неактивный
            'color': color,
            'extendedProps': {
                'comment': r.comment
            }
        })

    return jsonify(events)

@app.route('/requests')
def requests_route():
    role = session.get('role')
    if not role:
        return redirect(url_for('login'))

    if role == 'employee':
        user_id = session.get('user_id')
        requests = get_user_requests(user_id)
        return render_template('request_list.html', requests=requests, services={'get_user_by_id': get_user_by_id})
    
    elif role == 'manager':
        # Для менеджера выводим заявки сотрудников его отдела
        user_id = session.get('user_id')
        all_requests = get_all_requests()
        # Фильтруем по отделу менеджера, если нужно
        requests = [r for r in all_requests if get_user_by_id(r.user_id).manager_id == user_id]
        return render_template('request_list.html', requests=requests, services={'get_user_by_id': get_user_by_id})

    elif role == 'hr':
        requests = get_all_requests()
        departments = get_departments_dict()
        return render_template('request_list.html', requests=requests, services={'get_user_by_id': get_user_by_id}, departments=departments)

    return redirect(url_for('login'))
# --- Календарь отдела ---
@app.route('/calendar')
def calendar_view():
    # Здесь можно рендерить шаблон с calendar.js
    return render_template('calendar.html')

@app.route('/manager')
def manager_dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    requests = get_all_requests()

    # передаем services в шаблон
    return render_template('manager_requests.html',
                           requests=requests,
                           services={'get_user_by_id': get_user_by_id})

@app.route('/manager/requests')
def manager_requests():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    all_requests = get_all_requests()
    # Фильтруем по отделу менеджера, если нужно
    requests = [r for r in all_requests if get_user_by_id(r.user_id).manager_id == user_id]

    return render_template('manager_requests.html',
                           requests=requests,
                           services={'get_user_by_id': get_user_by_id})

@app.route('/hr')
def hr_dashboard():
    if session.get('role') != 'hr':
        return redirect(url_for('login'))
    requests = get_all_requests()
    departments = get_departments_dict()
    return render_template('hr_requests.html', requests=requests, departments=departments, services={'get_user_by_id': get_user_by_id})

@app.route('/hr/export_csv')
def hr_export_csv():
    if session.get('role') != 'hr':
        return redirect(url_for('login'))

    requests = get_all_requests()
    departments = get_departments_dict()

    output = io.StringIO()
    writer = csv.writer(output)
    # Заголовки CSV
    writer.writerow(['Сотрудник', 'Отдел', 'Дата начала', 'Дата окончания', 'Дней', 'Тип', 'Статус'])

    for r in requests:
        user = get_user_by_id(r.user_id)
        dept_name = departments[user.department_id].name if user.department_id in departments else ''
        start = r.start_date
        end = r.end_date
        days = (end - start).days + 1
        writer.writerow([user.full_name, dept_name, start.isoformat(), end.isoformat(), days, r.type, r.status])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),  # UTF-8 с BOM, чтобы Excel корректно отображал русские буквы
        mimetype='text/csv',
        as_attachment=True,
        download_name='vacations.csv'
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)