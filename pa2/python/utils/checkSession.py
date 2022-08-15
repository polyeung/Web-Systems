import time
def sessionExists(session):
	if 'username' in session and 'lastActivity' in session:
		return True;
	return False;

def sessionIsValid(session):
	if 'username' in session and not sessionIsExpired(session):
			return True
	return False

def renewSession(session):
	session['lastActivity'] = int(time.time())

def sessionIsExpired(session):
	currentTime = int(time.time())
	if 'lastActivity' in session:
		if currentTime - session['lastActivity'] <= 300:
			# print currentTime - session['lastActivity']
			return False
	return True

def getUserInfoFromSession(session, mysql):
	if 'username' in session:
		ur = mysql.connection.cursor()
		cur.execute("SELECT * FROM User WHERE User.username = '%s'" %(session['username']))
		msgs = cur.fetchall()
		if msgs:
			return msgs
	return [[]]

def checkAccessibilityOfSession(session, mysql, albumid):
	if 'username' in session:
		ur = mysql.connection.cursor()
		cur.execute("SELECT * FROM AlbumAccess WHERE username = '%s' AND albumid = '%s'" %(session['username'], albumid))
		msgs = cur.fetchall()
		if msgs:
			return True
	return False
