# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired


class AdminLoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])


class CodeForm(FlaskForm):
    username = StringField('Имя участника', validators=[DataRequired()])
    drink = SelectField(
        'Энергетик',
        choices=[(f'energetik{i}', f'energetik{i}') for i in range(1, 11)],
        validators=[DataRequired()]
    )


class ReviewForm(FlaskForm):
    username = HiddenField(validators=[DataRequired()])
    drink = HiddenField(validators=[DataRequired()])
    text = TextAreaField('Ваш отзыв', validators=[DataRequired()])
