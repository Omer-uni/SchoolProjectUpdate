from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gelistirme_anahtari'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


tickets = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        firstname = current_user.firstname
        lastname = current_user.lastname
        email = current_user.email
        priority = request.form['priority']
        subject = request.form['subject']
        message = request.form['message']
        file = request.files.get('file')

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        ticket = {
            'id': len(tickets) + 1,
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'priority': priority,
            'subject': subject,
            'message': message,
            'file': filename,
            'status': 'İnceleme Bekliyor'
        }
        tickets.append(ticket)
        return render_template('ticket_created.html', ticket=ticket)
    return render_template('create_ticket.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_tickets = [t for t in tickets if t['email'] == current_user.email]
    return render_template('dashboard.html', tickets=user_tickets)

@app.route('/ticket/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if not ticket:
        return "Ticket bulunamadı", 404
    return render_template('ticket_detail.html', ticket=ticket)

@app.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if not ticket:
        return "Ticket bulunamadı", 404
    if request.method == 'POST':
        ticket['subject'] = request.form['subject']
        ticket['message'] = request.form['message']
        ticket['status'] = request.form['status']
        return redirect(url_for('ticket_detail', ticket_id=ticket_id))
    return render_template('edit_ticket.html', ticket=ticket)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta zaten kayıtlı!', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(firstname=firstname, lastname=lastname, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Giriş bilgileri hatalı!', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('Giriş başarılı!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yapıldı.', 'success')
    return redirect(url_for('index'))

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    global tickets
    tickets = [t for t in tickets if not (t['id'] == ticket_id and t['email'] == current_user.email)]
    flash('Ticket silindi.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
