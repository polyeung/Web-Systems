from utils import *
from flask import *
import hashlib
import os
import time

useredit = Blueprint('useredit', __name__, template_folder='views')

@useredit.route(appendKey('/user/edit'), methods=['GET', 'POST'])
def edit():
    username = ''
    con = mysql.connection
    cur = con.cursor()

    if request.method == 'GET':
    #auth code
        if not sessionExists(session):
            return render_template('noLogin.html', login=False), 403
        elif sessionIsExpired(session):
            session.clear()
            return render_template('sessionExpire.html', login=False)
        else:
            renewSession(session)
            username = session['username']
            cur.execute("SELECT * FROM User WHERE username='%s'"%(username))
            userinfo = cur.fetchall()
            if not userinfo:
                session.clear();
                return render_template('noLogin.html', login=False), 403
            else:
                options = {
                    "login": True,
                    "userinfo": userinfo[0]
                }

        return render_template("edit.html", **options)

    else:
        if not sessionExists(session):
            return render_template('noLogin.html', login=False), 403
        elif sessionIsExpired(session):
            session.clear()
            return render_template('sessionExpire.html', login=False)
        else:
            username = session['username']
            if request.form['password'] != request.form['re-password']:
                error = 'password does not match'
                return render_template('edit.html',error=error)

            hash_password = hashlib.sha224(request.form['password']).hexdigest()
            cur.execute("UPDATE User SET password ='%s', firstname = '%s', lastname='%s', email='%s' WHERE username='%s'" % (\
            hash_password, request.form['firstname'], request.form['lastname'], request.form['email'], username) )
            renewSession(session)
            con.commit()
            return redirect(url_for('main.main_route'))

        return render_template('edit.html', login=True)
