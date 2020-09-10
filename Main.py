import pymysql
from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import json
import os
import math
from datetime import datetime
from flask_mail import Mail
from werkzeug import secure_filename



with open("config.json","r")as c:
    params=json.load(c)["params"]
local_server = True
app = Flask(__name__)

app.secret_key = "Programming"
app.config["UPLOAD_FOLDER"]=params["upload_location"]
#Massage sent
app.config.update(
    MAIL_SERVER= 'smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["user_name"],
    MAIL_PASSWORD = params["password"]
)
mail = Mail(app)

if(local_server):
   app.config['SQLALCHEMY_DATABASE_URI']=params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)
#contact class
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)

#post class
class Posts(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    tag_line = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    date_post = db.Column(db.String(12), nullable=True)





#all pos fatch on Home
@app.route('/')
def hello():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    #[0:params["no_of_post"]]
    page= request.args.get('page')
    if( not str(page).isnumeric()):
        page=1
    page = int(page)
    posts=posts[(page -1)*int(params['no_of_post']):(page -1)*int(params['no_of_post'])+int(params['no_of_post'])]



    #Pagination
    #first
    if (page==1):
        prev ="#"
        next ="/?page=" + str(page +1)

    #last
    elif (page==last):
        prev = "/?page=" + str(page -1)
        next = "#"

    #middle
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)

#about
@app.route('/about')
def about():
    return render_template('about.html',params=params)



#dashboard
@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if('user' in session and session['user']== params["user_admin"]):
        posts = Posts.query.all()
        return  render_template('dashboard.html',params=params,posts=posts)


    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params["user_admin"] and userpass == params["admin_pwd"]):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params,posts=posts)

    return render_template('login.html',params=params)

#Add and Endit Post
@app.route("/edit/<string:s_no>",methods=['GET','POST'])
def edit(s_no):
    if ('user' in session and session['user'] == params["user_admin"]):
        if request.method=="POST":
            box_title=request.form.get("title")
            tag_line = request.form.get("tline")
            slug=request.form.get("slug")
            content=request.form.get("content")
            img_file=request.form.get("img_file")
            date = datetime.now()
            #date_post=request
            if s_no == "0":
                post=Posts(title=box_title,slug=slug,content=content,tag_line=tag_line,img_file=img_file,date_post=date)
                db.session.add(post)
                db.session.commit()
                redirect("/dashboard")

            else:
                post = Posts.query.filter_by(s_no=s_no).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tag_line = tag_line
                post.img_file = img_file
                post.date_post = date
                db.session.commit()
                return redirect('/edit/' + s_no)
        post = Posts.query.filter_by(s_no=s_no).first()
        return render_template("edit.html", params=params, s_no=s_no,post=post)



#file uploder
@app.route("/uploader",methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params["user_admin"]):
       if request.method == "POST":
           f = request.files['file1']
           f.save(os.path.join(app.config["UPLOAD_FOLDER"],
                                secure_filename(f.filename)))
           return "Uploaded Successfully"



#Blog Post
@app.route('/post/<string:post_slug>',methods=['GET'])
def post_root(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

#create Contact
@app.route('/contact', methods =['GET','POST'])
def contact():
    if (request.method=="POST"):
      name  =request.form.get('name1')
      email =request.form.get('email1')
      phone =request.form.get('phone1')
      message =request.form.get('message')

      entry=Contacts(name=name,email=email,phone=phone,msg=message,date=datetime.now())
      db.session.add(entry)
      db.session.commit()
      mail.send_message('New message from'+name,
                        sender= email,
                        recipients=[params['user_name']],
                        body=message +"\n"+phone)
    return render_template('contact.html',params=params)

#Logout
@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")

#Delete
@app.route("/delete/<string:s_no>",methods=['GET','POST'])
def delete(s_no):
  if ('user' in session and session['user'] == params["user_admin"]):
        post = Posts.query.filter_by(s_no=s_no).first()
        db.session.delete(post)
        db.session.commit()
  return redirect("/dashboard")


app.run(debug=True)