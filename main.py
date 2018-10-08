from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, validators, StringField, TextAreaField, PasswordField, ValidationError
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
    

#def valid_password(form, field):
 #    from run import config
 #   min_pwd_len = int(config['MIN_PWD_LEN'])
#    max_pwd_len = int(config['MAX_PWD_LEN'])
#    pass_size = len(field.data)
#    if pass_size == 0:
#        raise ValidationError('New password cannot be empty')
#    if pass_size < min_pwd_len or pass_size > max_pwd_len:
#        raise ValidationError(
#            'Password needs to be between {min_pwd_len} and {max_pwd_len} characters long (you entered {char})'.format(
#                min_pwd_len=min_pwd_len, max_pwd_len=max_pwd_len, char=pass_size)
#        )


class RegistrationForm(Form):
    name = StringField('Name', [validators.required(), validators.Length(min=3, max=25)])
    username = StringField('Username', [
        validators.Regexp(r'^[\w.@+-]+$', message='No special characters or spaces'), validators.Length(min=3, max=20)]
        )
    email = StringField('Email Address', [
        validators.Regexp(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', message='No special characters or spaces'),
        validators.Email(message='Please enter a valid email'),
        validators.Length(min=3)]
        )
    password = PasswordField('Password', [validators.Length(min=6, max=20, message='Password must be at least 6 characters'),
            validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])

    #password = PasswordField('Password', [ 
#        Data.Required(), 
#        EqualTo('confirm', message='Passwords must match'), 
#        Regexp(r'^[\w.@+-]+$', message='No special characters or spaces'),
#        Lenght(min=8, message='Password must be longer than 8 characters')
#    ])
    confirm = PasswordField('Confirm Password')

class ArticleForm(Form):
    title = StringField('Title', [validators.required(), validators.Length(min=3, max=25)])
    body = TextAreaField('Body', [validators.Length(min=30)])

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
    cur = mysql.connection.cursor()
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
    return render_template('login.html', title="Virtual Lobby")


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
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
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles, title="Blogs")
    else:
        msg = 'No blogs found'
        return render_template('dashboard.html', msg=msg, title="Blogs")
    cur.close()

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))
        mysql.connection.commit()
        cur.close()
        flash('Blog created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    form = ArticleForm(request.form)
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        cur = mysql.connection.cursor()
        app.logger.info(title)
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form, title="Edit Blog")


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Blog deleted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/about')
def about():
    return render_template('about.html', title="About")


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)