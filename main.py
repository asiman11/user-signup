from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL

from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'car0lina'
app.config['MYSQL_DB'] = 'virtuallobby'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Initialize MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html', title="Virtual Lobby :: Login")
    
class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    username = StringField('Username', [validators.Length(min=3, max=20)])
    email = StringField('Email Address', [validators.Length(min=3, max=20)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
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

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('signup.html', title="Virtual Lobby :: Signup", form=form)


@app.route('/about')
def about():
    return render_template('about.html', title="Virtual Lobby :: About")


@app.route('/contact')
def contact():
    return render_template('contact.html', title="Virtual Lobby :: Contact")



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)