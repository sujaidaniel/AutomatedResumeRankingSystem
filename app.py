import os
from flask import Flask, flash, request, redirect, render_template,url_for
from flask import session as httpSession
from flask.wrappers import Response
from werkzeug.wrappers import response
from constants import file_constants as cnst
from processing import resume_matcher
from utils import file_utils
import docx
from os.path import join, dirname, realpath
import sqlalchemy as sqlal
from sqlalchemy import *
from sqlalchemy import select
from sqlalchemy.orm import *
from werkzeug.security import generate_password_hash, check_password_hash


engine = create_engine('sqlite:////Users/Rohit A/Desktop/ResumeRanker/rranker.sqlite.db', echo=True)
metadata = MetaData(engine)

users = Table('users', metadata, 
    Column('user_id', String, primary_key=True),
    Column('phone_no', String),
    Column('email_id', String),
    Column('passwd', String))

user_resume = Table('user_resume', metadata, 
    Column('user_id', String, primary_key=True),
    Column('resume', BLOB))


class Users(object):
    def __init__(self, userId, phNo, email, pwd) -> None:
        self.user_id = userId
        self.phone_no = phNo
        self.email_id = email
        self.passwd = pwd

class UserResume(object):
    def __init__(self, userId, resume) -> None:
        self.user_id = userId
        self.resume = resume

mapper(Users, users);
mapper(UserResume, user_resume)
session = sessionmaker(engine)()


    

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','docx'])
app = Flask(__name__)
app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = cnst.UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define upload directory in the same project path.
uploads_dir = os.path.join(app.instance_path, 'uploads')
os.makedirs(uploads_dir, exist_ok = True)

def read_file(filename):
    print('Filename: ' + filename)
    with open(filename, 'rb') as f:
        resume = f.read()
    return resume

#API for creating user. 
@app.route('/user/create', methods=['POST'])
def create_user():
    if request.method == 'POST':
        #resume_file = request.files['resume']

        new_user = Users(request.form['user_id'], 
        request.form['phone_no'],
        request.form['email_id'],
        request.form['passwd']
        )

        session.add(new_user)
        session.commit()
        return render_template('login.html')

@app.route('/resume/save', methods=['POST'])
def resume_save():
    if request.method == 'POST':
        resume_file = request.files['resume']
        print("Resume complete path: " + os.path.join(uploads_dir, resume_file.filename))
        resume_data = read_file(os.path.join(uploads_dir, resume_file.filename))
        if 'user_id' not in httpSession:
            return 'User_id not in session'
        userId = httpSession['user_id']
        new_user_resume = UserResume(userId,
        resume_data
        )

        session.add(new_user_resume)
        session.commit()
        return 'Resume Saved Successfully !'

@app.route('/resume/delete', methods=['DELETE'])
def resume_delete():
    if request.method == 'DELETE':
        query ="DELETE  FROM user_resume WHERE user_id = '" + request.form['user_id'] + "'"

        engine.execute(query)
        
        print(query)
        return render_template('basePage.html')



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/loginCheck', methods=['GET', 'POST'])
def login_check():
    givenUserId = request.form['user_id']
    givenPwd = request.form['passwd']
    stmt = select(users.columns.passwd).where(users.columns.user_id == givenUserId)
    httpSession['user_id'] = givenUserId
    connection = engine.connect()
    results = connection.execute(stmt).fetchall()
    if results[0].passwd == givenPwd:
        return render_template('user.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/forgotPswd')
def forgot_pwd():
    return render_template('forgotPswd.html')

@app.route('/resumeRanker')
def upload_form():
    return render_template('resume_loader.html')

@app.route('/userPage')
def user_page():
    return render_template('user.html')

@app.route('/failure')
def failure():
   return 'No files were selected'

@app.route('/success/<name>')
def success(name):
   return 'Files %s has been selected' %name

@app.route('/resumeRanker', methods=['POST', 'GET'])
def check_for_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'reqFile' not in request.files:
           flash('Requirements document can not be empty')
           return redirect(request.url)
        if 'resume_files' not in request.files:
           flash('Select at least one resume File to proceed further')
           return redirect(request.url)
        file = request.files['reqFile']
        if file.filename == '':
           flash('Requirement document has not been selected')
           return redirect(request.url)
        resume_files = request.files.getlist("resume_files")
        if len(resume_files) == 0:
            flash('Select atleast one resume file to proceed further')
            return redirect(request.url)
        if ((file and allowed_file(file.filename)) and (len(resume_files) > 0)):
           #filename = secure_filename(file.filename)
           abs_paths = []
           filename = file.filename
           req_document = cnst.UPLOAD_FOLDER+'\\'+filename
           file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
           for resumefile in resume_files:
               filename = resumefile.filename
               abs_paths.append(cnst.UPLOAD_FOLDER + '\\' + filename)
               resumefile.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
           result = resume_matcher.process_files(req_document,abs_paths)
           for file_path in abs_paths:
               def delete_file(file_path):
                    os.remove(file_path)
                    delete_file(file_path)
           return render_template("resume_results.html", result=result)
        else:
           flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
           return redirect(request.url)

if __name__ == "__main__":
    app.run(debug = True)