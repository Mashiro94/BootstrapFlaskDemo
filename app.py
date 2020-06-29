# -*- coding: utf-8 -*-
from datetime import datetime

from flask import Flask, render_template, request, flash, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import DataRequired, Length

from dbSqlite3 import *

app = Flask(__name__)
app.secret_key = 'dev'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


class HelloForm(FlaskForm):
    username = StringField(u'用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField(u'密码', validators=[Length(0, 10)])
    select = SelectField(u'身份', choices=[('student', 'Student'), ('teacher', 'Teacher')])
    submit = SubmitField(u'登录')


class AccountForm(FlaskForm):
    secret = PasswordField(u'旧密码', validators=[DataRequired(), Length(0, 10)], render_kw={'placeholder': '旧密码'})
    password = PasswordField(u'新密码', validators=[DataRequired(), Length(0, 10)], render_kw={'placeholder': '新密码'})
    submit = SubmitField(u'修改密码')


class SelectForm(FlaskForm):
    title = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    submit = SubmitField(u'选课')


class DeleteForm(FlaskForm):
    title = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    submit = SubmitField(u'退课')


class ScoreForm(FlaskForm):
    title_sno = StringField(u'学生号', render_kw={'placeholder': '学生号'})
    title_cno = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    title_score = StringField(u'分数', render_kw={'placeholder': '分数'})
    submit = SubmitField(u'录入')


# 登录页
@app.route('/', methods=['GET', 'POST'])
def index():
    form = HelloForm()
    if request.method == "GET":
        return render_template('index.html', form=form)

    if form.validate_on_submit():
        if form.select.data == 'student':
            result, _ = GetSql2("select * from student where sno='%s'" % form.username.data)
            if not result:
                flash(u'用户名不存在', 'warning')
                return render_template('index.html', form=form)

            if result[0][5] == form.password.data:
                return render_template('student.html', sno=form.username.data)
            else:
                flash(u'密码错误', 'warning')
                return render_template('index.html', form=form)

        if form.select.data == 'teacher':
            result, _ = GetSql2("select * from teacher where tno='%s'" % form.username.data)
            if not result:
                flash(u'用户名不存在', 'warning')
                return render_template('index.html', form=form)

            if result[0][2] == form.password.data:
                return render_template('teacher.html', tno=form.username.data)
            else:
                flash(u'密码错误', 'warning')
                return render_template('index.html', form=form)


# 学生主页
@app.route('/student/<int:sno>', methods=['GET', 'POST'])
def student(sno):
    return render_template('student.html', sno=sno)


# 基本信息查看、学生个人登录密码修改功能
@app.route('/student/<int:sno>/account', methods=['GET', 'POST'])
def student_account(sno):
    form = AccountForm()

    result, _ = GetSql2("select * from student where sno='%s'" % sno)
    name = result[0][1]
    gender = result[0][2]
    birthday = result[0][3]
    birthtime = datetime.fromtimestamp(result[0][3] / 1000.0).strftime('%Y-%m-%d')
    major = result[0][4]

    if form.validate_on_submit():
        result, _ = GetSql2("select * from student where sno='%s'" % sno)
        if form.secret.data == result[0][5]:
            data = dict(
                sno=sno,
                name=name,
                gender=gender,
                birthday=birthday,
                major=major,
                password=form.password.data
            )
            UpdateData(data, "student")
            flash(u'修改成功！', 'success')
        else:
            flash(u'原密码错误', 'warning')

    return render_template('student_account.html', sno=sno, name=name, gender=gender, birthday=birthtime,
                           major=major, form=form)


# 学生选课功能
@app.route('/student/<int:sno>/course_select', methods=['GET', 'POST'])
def student_course_select(sno):
    form = SelectForm()

    result_course, _ = GetSql2("select * from course")

    messages = []
    for i in result_course:
        result_teacher = GetSql2("select name from teacher where tno='%s'" % i[2])
        result_score = GetSql2("select count(*) from score where cno='%s'" % i[0])
        message = {'cno': i[0], 'name': i[1], 'tname': result_teacher[0][0][0], 'count': result_score[0][0][0]}
        messages.append(message)

    titles = [('cno', '课程号'), ('name', '课程名'), ('tname', '任课教师'), ('count', '已选课人数')]

    if form.validate_on_submit():
        if not form.title.data:
            flash(u'请填写课程号', 'warning')
        else:
            result, _ = GetSql2("select * from course where cno='%s'" % form.title.data)
            if not result:
                flash(u'课程不存在', 'warning')
            else:
                result, _ = GetSql2("select * from score where sno='%s' and cno='%s'" % (sno, form.title.data))
                if result:
                    flash(u'课程选过了', 'warning')
                else:
                    data = dict(
                        sno=sno,
                        cno=form.title.data
                    )
                    InsertData(data, "score")
                    flash('选课成功', 'success')

    return render_template('student_course_select.html', sno=sno, messages=messages, titles=titles, form=form)


# 学生退课功能
@app.route('/student/<int:sno>/course_delete', methods=['GET', 'POST'])
def student_course_delete(sno):
    form = DeleteForm()

    result_score, _ = GetSql2("select * from score where sno='%s'" % sno)

    messages = []
    for i in result_score:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[1])
        result_teacher, _ = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        message = {'cno': i[1], 'cname': result_course[0][1], 'tname': result_teacher[0][1]}
        messages.append(message)

    titles = [('cno', '已选课程号'), ('cname', '课程名'), ('tname', '任课教师')]

    if form.validate_on_submit():
        if not form.title.data:
            flash(u'请填写课程号', 'warning')
        else:
            result, _ = GetSql2("select * from score where cno='%s' and sno='%s'" % (form.title.data, sno))
            if not result:
                flash(u'课程不存在', 'warning')
            else:
                DelDataById('sno', 'cno', sno, form.title.data, "score")
                flash('退课成功', 'success')
                return redirect(url_for('student_course_delete', sno=sno, messages=messages, titles=titles,
                                        form=form))

    return render_template('student_course_delete.html', sno=sno, messages=messages, titles=titles, form=form)


# 学生成绩查询功能
@app.route('/student/<int:sno>/score', methods=['GET', 'POST'])
def student_score(sno):
    result_score, _ = GetSql2("select * from score where sno='%s'" % sno)

    messages = []
    for i in result_score:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[1])
        result_teacher, _ = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        if not i[2]:
            message = {'cno': i[1], 'cname': result_course[0][1], 'tname': result_teacher[0][1], 'score': '无成绩'}
        else:
            message = {'cno': i[1], 'cname': result_course[0][1], 'tname': result_teacher[0][1], 'score': i[2]}
        messages.append(message)

    titles = [('cno', '已选课程号'), ('cname', '课程名'), ('tname', '任课教师'), ('score', '成绩')]

    return render_template('student_score.html', sno=sno, messages=messages, titles=titles)


# 老师主页
@app.route('/teacher/<int:tno>', methods=['GET', 'POST'])
def teacher(tno):
    return render_template('teacher.html', tno=tno)


# 老师个人登录密码修改功能
@app.route('/teacher/<int:tno>/account', methods=['GET', 'POST'])
def teacher_account(tno):
    form = AccountForm()

    if form.is_submitted():
        result, _ = GetSql2("select * from teacher where tno='%s'" % tno)
        if form.secret.data == result[0][2]:
            data = dict(
                tno=tno,
                name=result[0][1],
                password=form.password.data
            )
            UpdateData(data, "teacher")
            flash(u'修改成功！', 'success')
        else:
            flash(u'原密码错误', 'warning')

    return render_template('teacher_account.html', tno=tno, form=form)


# 老师开课信息查看（开设课程基本信息、开设课程学生名单）
@app.route('/teacher/<int:tno>/course', methods=['GET', 'POST'])
def teacher_course(tno):
    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    messages = []
    for i in result_course:
        message = []
        result_score, _ = GetSql2("SELECT sno FROM score WHERE cno='%s'" % i[0])
        if not result_score:
            continue
        else:
            for j in result_score:
                result_student, _ = GetSql2("select * from student where sno='%s'" % j[0])
                row = {'cno': i[0], 'cname': i[1], 'sno': result_student[0][0], 'name': result_student[0][1],
                       'gender': result_student[0][2], 'major': result_student[0][4], }
                message.append(row)
        messages.append(message)

    titles = [('sno', '学员号'), ('name', '学员姓名'), ('gender', '性别'), ('major', '专业')]
    return render_template('teacher_course.html', tno=tno, messages=messages, titles=titles)


# 老师成绩录入和修改功能（手工录入）
@app.route('/teacher/<int:tno>/score', methods=['GET', 'POST'])
def teacher_score(tno):
    form = ScoreForm()

    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    messages = []
    for i in result_course:
        message = []
        result_score, _ = GetSql2("SELECT * FROM score WHERE cno='%s'" % i[0])
        for j in result_score:
            result_student, _ = GetSql2("select name from student where sno='%s'" % j[0])
            row = {'cname': i[1], 'cno': i[0], 'sno': j[0], 'name': result_student[0][0], 'score': j[2]}
            message.append(row)
        messages.append(message)

    titles = [('sno', '学员号'), ('name', '学员姓名'), ('score', '成绩')]

    if form.validate_on_submit():
        if not (form.title_cno.data and form.title_sno.data and form.title_score.data):
            flash(u'输入不完整', 'warning')
        else:
            result, _ = GetSql2(
                "select * from score where cno='%s' and sno='%s'" % (form.title_cno.data, form.title_sno.data))
            if result:
                data = dict(
                    sno=form.title_sno.data,
                    cno=form.title_cno.data,
                    score=form.title_score.data
                )
                UpdateData(data, "score")
                flash(u'录入成功！', 'success')
                return redirect(url_for('teacher_score', tno=tno, messages=messages, titles=titles, form=form))
            else:
                flash(u'该学生未选课', 'warning')

    return render_template('teacher_score.html', tno=tno, messages=messages, titles=titles, form=form)


# 成绩导入（新增和更新）功能（excel 文件导入）
# 这个需求会引发太多的Bug，需要execl严格遵守某种格式，故在目前的版本中暂不实现


if __name__ == '__main__':
    app.run()
