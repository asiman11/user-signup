from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title="Virtual Lobby :: Login")
    
@app.route('/signup')
def signup():
    return render_template('signup.html', title="Virtual Lobby :: Signup")


@app.route('/about')
def about():
    return render_template('about.html', title="Virtual Lobby :: About")


@app.route('/contact')
def contact():
    return render_template('contact.html', title="Virtual Lobby :: Contact")
app.run(debug = True)
