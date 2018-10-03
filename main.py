from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, validators, StringField, TextAreaField, PasswordField
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'virtuallobby'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Initialize MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html', title="Virtual Lobby")
    
class RegistrationForm(Form):
    name = StringField('Name', [validators.required(), validators.Length(min=3, max=25)])
    username = StringField('Username', [
        validators.Regexp(r'^[\w.@+-]+$', message='No special characters or spaces'), validators.Length(min=3, max=20)]
        )
    email = StringField('Email Address', [
        validators.Regexp(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', message='No special characters or spaces'),
        validators.Email(message='Please enter a valid email'),
        validators.Length(min=3, max=20)]
        )
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Regexp(r'^[\w.@+-]+$', message='No special characters or spaces'),
    ])
    confirm = PasswordField('Confirm Password')

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', title="Blogs", articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', title="No Blogs Found", msg=msg)
    # Close connection
    cur.close()

#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        flash('Congratulations, you are now registered and can log in', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', title="Register", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error, title="Login")
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error, title="Login")
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
 #   cur = mysql.connection.cursor()

    # Get articles
  #  result = cur.execute("SELECT * FROM articles")

   # articles = cur.fetchall()

    #if result > 0:
    return render_template('dashboard.html', articles=articles)
    #else:
     #   msg = 'No Articles Found'
      #  return render_template('dashboard.html', msg=msg)
    # Close connection
    #cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/about')
def about():
    return render_template('about.html', title="About")


@app.route('/contact')
def contact():
    return render_template('contact.html', title="Contact")



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)