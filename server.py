from flask import Flask, render_template, request, session, redirect, url_for
from databaseHandler import addUser, authenticate, fetchAllMessages, fetchAllUsers, isUserOnline, saveMessage, setUserLastSeen
import bleach

ALLOWED_TAGS = ['b', 'i', 'u', 's', 'strike', 'mark', 'strong', 'em', 'sub', 'sup', 'p', 'br', 'a', 'marquee', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'table', 'tbody', 'thead', 'tr', 'th', 'td', 'img', 'audio', 'video']
ALLOWED_ATTRS = {'a': ['href', 'title'], 'marquee': ['behavior', 'direction', 'scrollamount', 'scrolldelay'], 'table': ['border'], 'img': ['src', 'alt', 'width', 'height'], 'audio': ['src', 'controls'], 'video': ['src', 'controls'], 'video': ['src', 'controls']}

app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/')
def index():
    if session.get('user'):
        # print(fetchAllUsers())
        return render_template('index.html', user=session.get('user'), all_users=fetchAllUsers(session.get('user')['username']))
    else:
        return render_template('index.html')


@app.route('/sign-up', methods=['POST'])
def signup():
    if session.get('user'):
        return redirect(url_for('index'))
    user_info = (request.form.get('name'), request.form.get(
        'username'), request.form.get('pin'))
    if addUser(*user_info) is None:
        return render_template('index.html', signup_msg='username already exists', signup_error=True, redirect=True)
    return render_template('index.html', signup_msg='account created! u can sign-in now.', signup_error=False, redirect=True)


@app.route('/sign-in', methods=['POST'])
def signin():
    if session.get('user'):
        return redirect(url_for('index'))
    user_info = (request.form.get('username'), request.form.get('pin'))
    auth_result = authenticate(*user_info)
    if auth_result is None:
        return render_template('index.html', signin_msg='invalid username or pin', signin_error=True, redirect=True)
    else:
        session['user'] = auth_result
        # setLastSeen()
        return redirect(url_for('index'))

@app.route('/set_last_seen')
def setLastSeen():
    if session.get('user'):
        if setUserLastSeen(session.get('user')['username']):
            return "success"
        else:
            return "failure"
    else:
        return None

@app.route('/sign-out')
def signout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/chats/to=<to>?autofetch=<autofetch>')
def chats(to:str, autofetch:str="no"):
    if session.get('user'):
        messages = fetchAllMessages(sender=session.get('user')['username'], receiver=to)
        if autofetch == "yes":
            return render_template('partials/messages.html', messages=messages if messages is not None else [])
        # print(messages)
    # messages = [{"from":"me","message":"hello"},{"from":"you","message":"hi"}]
        return render_template('chats.html', to=to, user=session.get('user')['username'], status=isUserOnline(to), messages=messages if messages != None else [])
    else:
        return redirect(url_for('index'))

# @app.route('/send/to=<to>/message=<message>')
# def sendMessage(to:str, message:str):
#     print(f"{to}: {message}")
#     message = bleach.clean(message, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
#     message = bleach.linkify(message)
#     saveMessage(sender=session.get('user')['username'], receiver=to, message=message)
#     return redirect(url_for('chats', to=to))

@app.route('/send', methods=['POST'])
def sendMessage():
    message, to = (request.form.get('message'), request.form.get('to'))
    # print(f"{to}: {message}")
    message = bleach.clean(message, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
    message = bleach.linkify(message)
    saveMessage(sender=session.get('user')['username'], receiver=to, message=message)
    return redirect(url_for('chats', to=to, autofetch="yes"))
# if __name__ == '__main__':
#     app.run(debug=True)
