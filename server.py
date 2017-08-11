from flask import Flask, request, redirect, render_template ,flash,session
import re
import md5
# import the Connector function
from mysqlconnection import MySQLConnector
app = Flask(__name__)

app.secret_key = "twinjuan"
# connect and store the connection in "mysql" note that you pass the database name to the function
mysql = MySQLConnector(app, 'wall_db')
# an example of running a query
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]{2,}$')
PASSWORD_REGEX = re.compile(r'^.{8,}$')

@app.route('/')
def index():
    return render_template("index.html")
@app.route('/wall')
def home():
    query = "SELECT posts.id,posts.data , DATE_FORMAT(posts.update_time,'%M %D %Y') AS update_at, CONCAT(users.first_name,' ',users.last_name) AS name FROM posts JOIN users ON posts.user_id = users.id"
    posts = mysql.query_db(query)
    messages = {}
    for post in posts:
        query = "SELECT messages.data , DATE_FORMAT(messages.update_time,'%M %D %Y') AS update_at, CONCAT(users.first_name,' ',users.last_name) AS name FROM messages JOIN users ON messages.user_id = users.id JOIN posts ON messages.post_id = posts.id WHERE posts.id = :post_id"
        data = {
            "post_id" : post["id"],
        }
        message = mysql.query_db(query, data)
        messages[post["id"]] = message
    return render_template("wall.html",posts = posts, messages = messages)

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()
    query = "SELECT users.id,users.email, users.password, CONCAT(users.first_name,' ', users.last_name) as name FROM users where users.email = :email and users.password = :password"
    data = {
        "email" : email,
        "password" : password
    }
    info = mysql.query_db(query, data)

    if info:
        flash(info[0]["name"])
        session["user_id"] = info[0]['id']
        return redirect("/wall")

    flash("Invalid email and/or password! Failed to login")
    return redirect("/")

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    confirm = request.form['confirm']

    if len(email) < 1:
        flash("Email field not filled")
        return redirect("/")
    elif not EMAIL_REGEX.match(email):
        flash("Invalid email filled")
        return redirect("/")
    elif len(first_name) < 1:
        flash("First Name field not filled")
        return redirect("/")
    elif not NAME_REGEX.match(first_name):
        flash("First Name cannot contain digits")
        return redirect("/")
    elif len(last_name) < 1:
        flash("Last Name field not filled")
        return redirect("/")
    elif not NAME_REGEX.match(last_name):
        flash("Last Name cannot contain digits")
        return redirect("/")
    elif len(password) < 1:
        flash("Password field not filled")
        return redirect("/")
    elif not PASSWORD_REGEX.match(password):
        flash("Password needs to cotain atleast 1 digit and upper case letter and greater than 8 letters")
        return redirect("/")
    elif len(confirm) < 1:
        flash("Confirm password field not filled")
        return redirect("/")
    elif password != confirm:
        flash("Passwords don't match")
        return redirect("/")

        
    password = md5.new(password).hexdigest()
    query = "SELECT users.email as email, users.password as passwd, concat_ws(' ', users.first_name, users.last_name) as name FROM users where users.email = :email"
    data = {
        "email" : email,
        "first_name" : first_name,
        "last_name" : last_name,
        "password" : password
    }
    info = mysql.query_db(query, data)
    if info:
        flash("Email already exist in database!!")
        return redirect("/")

    query = "INSERT into users(users.first_name,users.last_name,users.email,users.password) value(:first_name,:last_name,:email,:password)"
    mysql.query_db(query, data)

    query = "SELECT * FROM users where users.email = :email"
    info = mysql.query_db(query, data)
    if not info:
        flash("Creation failed!")
        return redirect("/")

    session["user_id"] = info[0]['id']
    flash(first_name + " " + last_name)
    return redirect("/wall")

@app.route('/post', methods=['POST'])
def post():
    post = request.form['post']
    query = "INSERT into posts(posts.data,posts.user_id) value(:post,:id)"
    data = {
        "post" : post,
        "id" : session["user_id"],
    }
    info = mysql.query_db(query, data)
    return redirect("/wall")

@app.route('/comment', methods=['POST'])
def comment():
    post_id = request.form['post_id']
    comment = request.form['comment']
    query = "INSERT into messages(messages.data,messages.user_id,messages.post_id) value(:comment,:user_id, :post_id)"
    data = {
        "comment" : comment,
        "user_id" : session["user_id"],
        "post_id" : post_id,
    }
    info = mysql.query_db(query, data)
    return redirect("/wall")

app.run(debug=True)