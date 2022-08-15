from utils import *
from flask import *
import hashlib
import os
import time

album = Blueprint('album', __name__, template_folder='views')

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'bmp', 'gif'])
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, '../static/pictures')
def allowed_file(filename):
    lowerFileName = filename.lower()
    return '.' in lowerFileName and lowerFileName.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@album.route(appendKey('/album/edit'), methods=['GET', 'POST'])
def album_edit_route():
    error = ''
    albumid = request.args.get('id')
    if not albumid:
        abort(404)
    con = mysql.connection
    cur = con.cursor()
    cur.execute("SELECT albumid, username FROM Album WHERE albumid=%s"%(albumid))
    album = cur.fetchall()
    if not album:
        abort(404)

# Authentication Codes
    login = False
    if sessionExists(session):
        if sessionIsExpired(session):
            session.clear()
            return render_template('sessionExpire.html', login=False)
        else:
            login = True
            renewSession(session)
            if album[0][1] != session['username']:
                return render_template('noAccess.html', login=True), 403
    else:
        return render_template('noLogin.html', login=False), 403
# Authentication Codes End

    #add picture to static/pictures
    if request.method == 'POST':
        #add picture to static/pictures
        if request.form['op'] == 'add':
            file = ""
            if "file" in request.files:
               file = request.files['file']

            if file and allowed_file(file.filename):
                format = file.filename.rsplit('.', 1)[1]
                date = time.strftime('%Y-%m-%d', time.gmtime())
                curtime = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
                picid = hashlib.sha224(file.filename+curtime).hexdigest()
                picname = picid + '.' + format
                url = '/static/pictures/'+picname
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                file.save(os.path.join(UPLOAD_FOLDER,picname))


                seqnum = 1
                sqlphoto = "INSERT INTO Photo (picid, url, format, date) VALUES ('%s', '%s', '%s', '%s')" % (picid, url, format, date)
                cur.execute(sqlphoto)
                con.commit()

                cur.execute("SELECT MAX(sequencenum) FROM Contain WHERE Contain.albumid = %s" %(albumid))
                maxseq = cur.fetchall()[0][0]
                if maxseq:
                    seqnum = maxseq+1

                sqlcontain = "INSERT INTO Contain (albumid, picid, caption, sequencenum) VALUES(%s, '%s', '', %d )" %(albumid, picid, seqnum)
                cur.execute(sqlcontain)
                con.commit()

        if request.form['op'] == 'delete':
            picid = ""
            if "picid" in request.form:
               picid = request.form['picid']
            sqlcontain = "DELETE FROM Contain WHERE Contain.picid = '%s'" %(picid)
            cur.execute(sqlcontain)
            con.commit()

            sqlphoto = "SELECT url FROM Photo WHERE Photo.picid = '%s'" %(picid)
            cur.execute(sqlphoto)
            msgsurl = cur.fetchall()
            url = msgsurl[0][0]

            sqlphoto = "DELETE FROM Photo WHERE Photo.picid = '%s'" %(picid)
            cur.execute(sqlphoto)
            con.commit()

            url = ".." + url
            os.remove(os.path.join(APP_ROOT, url))

        if request.form['op'] == 'modifyAlbumName':
            if "albumName" in request.form:
               newAlbumName = request.form['albumName']
            sqlupdatealbumname = "UPDATE Album SET title = '%s' WHERE albumid = %s" %(newAlbumName, albumid)
            cur.execute(sqlupdatealbumname)
            con.commit()

        if request.form['op'] == 'revoke':
            username = ""
            if "username" in request.form:
               username = request.form['username']
            sqlrevoke = "DELETE FROM AlbumAccess WHERE username = '%s' AND albumid = '%s'" %(username, albumid)
            cur.execute(sqlrevoke)
            con.commit()

        if request.form['op'] == 'modifyAccess':
            privacy = ""
            if "privacy" in request.form:
               privacy = request.form['privacy']
            if privacy == 'private' or privacy == 'public':
                sqlrevoke = "UPDATE Album SET access = '%s' WHERE albumid = '%s'" %(privacy, albumid)
                cur.execute(sqlrevoke)
                if privacy == 'public':
                    sql_delete_access = "DELETE FROM AlbumAccess WHERE albumid = %s"%(albumid)
                    cur.execute(sql_delete_access)
                con.commit()

        if request.form['op'] == 'addAccess':
            username = ""
            if "username" in request.form:
               username = request.form['username']
            findUser = "SELECT * FROM User WHERE username = '%s'" %(username)
            cur.execute(findUser)
            user = cur.fetchall()
            if not user:
                error = 'No such a user.'
            else:
                findAccess = "SELECT * FROM AlbumAccess WHERE username = '%s' AND albumid = %s" %(username, albumid)
                cur.execute(findAccess)
                access = cur.fetchall()
                if access:
                    error = 'User already has authentication'
                else:
                    sqladd = "INSERT INTO AlbumAccess(albumid, username) Values (%s, '%s')" %(albumid, username)
                    cur.execute(sqladd)
                    con.commit()

    cur.execute("SELECT Photo.picid, url, Contain.caption, date FROM Photo, Contain WHERE Photo.picid = Contain.picid AND Contain.albumid = '%s' ORDER BY sequencenum "%(albumid))

    photos = cur.fetchall()
    cur.execute("SELECT username, title, access FROM Album WHERE albumid = %s" %(albumid))
    albumInfo = cur.fetchall()
    cur.execute("SELECT username FROM AlbumAccess WHERE albumid = %s" %(albumid))
    accessUsers = cur.fetchall()
    options = {
        "edit": True,
        "photos": photos,
        "username": albumInfo[0][0],
        "albumname":albumInfo[0][1],
        "privacy": albumInfo[0][2],
        "albumid": albumid,
        "login": login,
        "error": error,
        "accessUsers": accessUsers
    }
    return render_template("album.html", **options)

@album.route(appendKey('/album'), methods = ['GET'])
def album_route():

    albumid = request.args.get('id')
    if not albumid:
        abort(404)
    cur = mysql.connection.cursor()
    cur.execute("SELECT albumid, username, access FROM Album WHERE albumid=%s"%(albumid))
    album = cur.fetchall()
    if not album:
        abort(404)

# Authentication Codes
    login = False
    if album[0][2] == 'private':
        if sessionExists(session):
            if sessionIsExpired(session):
                session.clear();
                return render_template('sessionExpire.html', login=False)
            else:
                login = True
                if album[0][1] == session['username']:
                    renewSession(session)
                else:
                    cur.execute("SELECT username FROM AlbumAccess WHERE albumid=%s and username='%s'"%(albumid, session['username']))
                    authUser = cur.fetchall()
                    renewSession(session)
                    if not authUser:
                        return render_template('noAccess.html', login=True), 403
        else:
            return render_template('noLogin.html', login=False), 403
    else:
        if sessionExists(session):
            if sessionIsExpired(session):
                print 'session expired'
                session.clear();
            else:
                login = True
                renewSession(session)
# Authentication Codes End

    cur.execute("SELECT Photo.picid, url, Contain.caption, date FROM Photo, Contain WHERE Photo.picid = Contain.picid AND Contain.albumid = '%s' ORDER BY sequencenum "%(albumid))
    photos = cur.fetchall()
    cur.execute("SELECT username, title FROM Album WHERE albumid = '%s'" %(albumid))
    albumInfo = cur.fetchall()
    options = {
        "edit": False,
        "photos": photos,
        "username": albumInfo[0][0],
        "albumname":albumInfo[0][1],
        "albumid": albumid,
        "login": login
    }
    # print options
    return render_template("album.html", **options)
