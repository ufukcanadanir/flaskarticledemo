import email
from unicodedata import name
from click import password_option
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from sympy import Id
from wtforms import Form, StringField, PasswordField, TextAreaField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# User Log In Decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayi goruntulemek icin lutfen giris yapin.", "danger")
            return redirect(url_for("login"))
    return decorated_function


# User Registration Form


class RegisterForm(Form):
    name = StringField("Isim Soyisim", validators=[
                       validators.Length(min=4, max=25)])
    username = StringField("Kullanici Adi", validators=[
                           validators.Length(min=4, max=16)])
    email = StringField("Email", validators=[validators.Email(
        message="Lutfen gecerli bir email adresi giriniz.")])
    password = PasswordField("Parolanizi Giriniz: ", validators=[validators.DataRequired(
        message="Lutfen bir parola giriniz"), validators.EqualTo(fieldname="confirm", message="Parolaniz uyusmuyor")])
    confirm = PasswordField("Parolanizi Dogrulayiniz: ", validators=[validators.DataRequired(
        message="Lutfen parolanizi tekrar giriniz"), validators.EqualTo(fieldname="password", message="Parolaniz uyusmuyor")])

# Login Form


class LoginForm(Form):
    username = StringField("Kullanici Adi: ")
    password = PasswordField("Sifre: ")


app = Flask(__name__)
# Creating a secret key
app.secret_key = "uablog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "uablog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

# Connecting app to MySQL

mysql = MySQL(app)


@ app.route("/")
def index():
    articles = [{"id": 1, "title": "Deneme 1", "context": "Deneme 1 Icerik"},
                {"id": 2, "title": "Deneme 2", "context": "Deneme 2 Icerik"},
                {"id": 3, "title": "Deneme 3", "context": "Deneme 3 Icerik"},
                {"id": 4, "title": "Deneme 4", "context": "Deneme 4 Icerik"}]
    return render_template("index.html", answer="evet", articles=articles)


@ app.route("/about")
def about():
    return render_template("about.html")


# Detay Sayfasi  Dinamik urller
@app.route("/article/<string:id>")
def detailedArticle(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu, (id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")

# Dashboard


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * from articles where author =%s"
    result = cursor.execute(sorgu, (session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")

# Register


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        # Adding registration datas to MySQL database
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        # Creating a cursor to manipulate database
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users (name,email,username,password) Values(%s,%s,%s,%s)"
        cursor.execute(sorgu, (name, email, username, password))
        mysql.connection.commit()
        cursor.close()

        # MESSAGE FLASHING
        flash("Basariyla kayit oldunuz", "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

# Login


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        # creating cursor to logging in
        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Basariyla giris yaptiniz...", "success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Sifre hatali...", "danger")
                return redirect(url_for("login"))

        else:
            flash("Boyle bir kullanici bulunmamakta", "danger")
            return redirect(url_for("login"))

    else:
        return render_template("/login.html", form=form)

# Logout


@app.route("/logout")
def logout():
    session.clear()
    flash("Basariyla cikis yaptiniz", "success")
    return redirect(url_for("index"))


# Article page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")

# Adding Articles


@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form .content.data
        cursor = mysql.connection.cursor()
        sorgu = "INSERT into articles(title, author, content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale basariyla eklendi", "success")
        return redirect(url_for("dashboard"))
    return render_template("/addarticle.html", form=form)


# Deleting Article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu, (session["username"], id))
    if result > 0:
        sorgu2 = "DELETE FROM articles where id = %s"
        cursor.execute(sorgu2, (id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Boyle bir makale yok veya bu isleme yetkiniz bulunmamakta", "danger")
        return redirect(url_for("index"))
        # Article Form


class ArticleForm(Form):
    title = StringField("Baslik", validators=[
                        validators.Length(min=5, max=100)])
    content = TextAreaField("Icerik", validators=[validators.Length(min=10)])


if __name__ == "__main__":
    app.run(debug=True)
