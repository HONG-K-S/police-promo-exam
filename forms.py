from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('아이디', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class AdminLoginForm(FlaskForm):
    username = StringField('관리자 아이디', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('관리자 로그인')

class UserEditForm(FlaskForm):
    name = StringField('이름', validators=[DataRequired(), Length(min=2, max=50)])
    rank = StringField('계급', validators=[DataRequired(), Length(max=50)])
    department = StringField('부서', validators=[DataRequired(), Length(max=100)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    phone = StringField('전화번호', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('새 비밀번호', validators=[Optional(), Length(min=6, message='비밀번호는 최소 6자 이상이어야 합니다.')])
    password2 = PasswordField('비밀번호 확인', validators=[EqualTo('password', message='비밀번호가 일치하지 않습니다.')])
    is_admin = BooleanField('관리자 권한')
    is_active = BooleanField('활성화')
    submit = SubmitField('저장')
    cancel = SubmitField('취소') 