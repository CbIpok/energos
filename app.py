# app.py
import os
import uuid
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from models import db, Admin, Code, Review, Like
from forms import AdminLoginForm, CodeForm, ReviewForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password_hash=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and check_password_hash(admin.password_hash, form.password.data):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Неверные данные', 'danger')
    return render_template('login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    form = CodeForm()
    codes = Code.query.order_by(Code.id.desc()).all()
    return render_template('dashboard.html', form=form, codes=codes)

@app.route('/admin/generate_code', methods=['POST'])
@admin_required
def admin_generate_code():
    form = CodeForm()
    if form.validate_on_submit():
        new_code = str(uuid.uuid4()).split('-')[0]
        code = Code(code=new_code,
                    username=form.username.data,
                    drink=form.drink.data,
                    used=False)
        db.session.add(code)
        db.session.commit()
        flash(f'Сгенерирован код: {new_code}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/', methods=['GET', 'POST'])
def index():
    # Получаем все отзывы
    reviews = Review.query.all()
    # Считаем лайки для каждого отзыва
    likes_count = {r.id: Like.query.filter_by(review_id=r.id).count() for r in reviews}
    # Сортируем отзывы по убыванию числа лайков
    reviews.sort(key=lambda r: likes_count.get(r.id, 0), reverse=True)

    if request.method == 'POST':
        code_value = request.form.get('code')
        code = Code.query.filter_by(code=code_value, used=False).first()
        if code:
            session['code'] = code.code
            session['username'] = code.username
            session['drink'] = code.drink
            session['likes_used'] = 0
            return redirect(url_for('submit_review'))
        flash('Неверный или уже использованный код', 'danger')

    return render_template('index.html', reviews=reviews, likes_count=likes_count)

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if not session.get('code'):
        return redirect(url_for('index'))
    form = ReviewForm()
    form.drink.data = session['drink']
    form.username.data = session['username']
    if form.validate_on_submit():
        review = Review(username=form.username.data,
                        drink=form.drink.data,
                        text=form.text.data)
        db.session.add(review)
        code = Code.query.filter_by(code=session['code']).first()
        code.used = True
        db.session.commit()
        session['likes_used'] = 0
        flash('Отзыв успешно отправлен!', 'success')
        return redirect(url_for('index'))
    return render_template('submit_review.html', form=form)

@app.route('/like/<int:review_id>', methods=['POST'])
def like(review_id):
    code_str = session.get('code')
    if not code_str:
        flash('Чтобы лайкать, сперва введите код участника', 'warning')
        return redirect(url_for('index'))

    code = Code.query.filter_by(code=code_str).first()
    # нельзя лайкать один и тот же отзыв этим кодом дважды
    if Like.query.filter_by(code_id=code.id, review_id=review_id).first():
        flash('Вы уже лайкали этот отзыв', 'warning')
    elif session.get('likes_used', 0) >= 1:
        flash('Вы использовали свой лайк. Чтобы получить новый — оставьте отзыв.', 'warning')
    else:
        review = Review.query.get_or_404(review_id)
        if review.username == session['username']:
            flash('Нельзя лайкать собственный отзыв', 'warning')
        else:
            like_obj = Like(review_id=review_id, code_id=code.id, username=session['username'])
            db.session.add(like_obj)
            db.session.commit()
            session['likes_used'] = session.get('likes_used', 0) + 1
            flash('Лайк учтён', 'success')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
