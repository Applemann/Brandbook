#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mod_python import apache, psp, Session, util
import cgi, MySQLdb, re
from time import gmtime, strftime
import hashlib, binascii


HOME = "/home/martin/Projekty/Brandbook/"
LAYOUT = "layout.html"
DOMAIN = "http://brandbook.localhost.cz"
req = None
SESSION = {}

def _get_database():
	return MySQLdb.connect("localhost","root","b5huha57","online_textovky")

def _get_datetime():
	return strftime("%Y-%m-%d %H:%M:%S", gmtime())

def _get_time():
	time = strftime("%H:%M:%S", gmtime())
	if time[0]=="0":
		return time[1:]
	else:
		return time

def _create_hash(password, datetime):
	salt = datetime+"*mllkeúor.-§ǘ*"
	h = hashlib.new('sha1')
	h.update(password+salt)
	return h.hexdigest()

def _open_view(file):
	f = open(file, "r")
	view = f.read()
	f.close()
	return view
	
def _is_valid_email(email):
	return re.match(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', str(email)) != None
	

def _get_partial_view(file, model):
	content = _open_view(HOME+file)
	for key, value in model.iteritems():
		content = content.replace("<%="+key+"%>", value)
	return content

def _set_view(req, model={}, layout=LAYOUT):
	tmpl = psp.PSP(req, layout)
	tmpl.run(vars = model, flush=False)
	
def _get_template(req, file):
	return psp.PSP(req, file)

def _login(email, password):
	
	db = _get_database()
	c = db.cursor()
	c.execute("select email, password_hash, created from users")
	for (mail, hash, created) in c.fetchall():
		if email == mail and _create_hash(password, str(created)) == hash:
			return True
	db.commit()
	db.close()
	
	return False

##########################################################

def __init__(self):
	pass

def index(req, flashmessage=""):
	content = _get_partial_view("content.html", { "flashmessage":flashmessage})
	_set_view(req, { "content":content})
	
def show_index(flashmessage=""):
	index(req, flashmessage)
	
def save_user(email, password):
	try:
		nick = email#.split("@")[0]
		db = _get_database()
		c = db.cursor()
		datetime = _get_datetime()
		password_hash = _create_hash(password, datetime)
		c.execute("INSERT INTO users (nick, email, password_hash, created) VALUES (%s,%s,%s,%s);", (nick, email, password_hash, datetime))
		db.commit()
		db.close()
		return True
	except Exception, ex:
		return False
		

def register(req, root):
	if(req.uri == root):
		show_registration(req, "")
	elif(req.uri == root+"_send"):
		form = util.FieldStorage(req)
		email = form.getfirst("email")
		pass1 = form.getfirst("pass1")
		pass2 = form.getfirst("pass2")
		flashmessage = ""
		
		if not _is_valid_email(email):
			flashmessage += "Špatně zadaný email.<br/>"
		if (pass1 != None and len(pass1) < 8):
			flashmessage += "Heslo musí být dlouhé alespoň 8 znaků.<br/>"
		if (pass1 != pass2):
			flashmessage += "Hesla se musí shodovat.<br/>"
		if (flashmessage != ""):	
			show_registration(req,flashmessage)
		else:
			if(save_user(email, pass1)):
				flashmessage += "Registrace proběhla úspěšně. Nyní se můžete přihlásit.<br/>"
				req.uri = "/login"
				show_login(req,flashmessage)
			else:
				flashmessage += "Někde se stala nějaká neznámá chyba, kontaktujte admina: admin@brandbook.cz<br/>"
				show_registration(req,flashmessage)
		

def show_registration(req,flashmessage=""):
	_set_view(req, {"flashmessage":flashmessage}, layout="registration.html")

def show_login(req,flashmessage=""):
	_set_view(req, {"flashmessage":flashmessage}, layout="login.html")

def login(req, root):
	if(req.uri == root+"_send"):
		form = util.FieldStorage(req)
		email = form.getfirst("email")
		password = form.getfirst("password")
		flashmessage = ""
		
		if _login(email, password):
			SESSION["user"] = email
			SESSION.save()
			util.redirect(req, DOMAIN+"/index")
		else:
			flashmessage += "Přihlášení proběhlo neúspěšně. Email nebo heslo není správně.<br/>"
			show_login(req, flashmessage)
		
	elif(req.uri == root):
		show_login(req)
	
def chat(req, root):
	if (req.uri == root+"/send_post"):
		form = util.FieldStorage(req)
		message = form.getfirst("message")
		user = form.getfirst("user")
		
		db = _get_database()
		c = db.cursor()
		
		c.execute("select id from users where nick=%s;", (user,))
		c.execute("INSERT INTO messages VALUES (%s,%s,%s);", (c.fetchone()[0], _get_time(), message))
		db.commit()
		db.close()
		
		return "[%s] %s: %s <br/>\n" % (_get_time(), user, message)
		
	elif(req.uri == root):
		db = _get_database()
		c = db.cursor()
		
		c.execute("select * from messages;")
		messages = c.fetchall()[-10:]
		lines = ""
		
		for message in messages:
			(user , time, text) = message
			c.execute("select nick from users where id=%s;", (user,))
			user = c.fetchone()[0]
			lines += "[%s] %s: %s <br/>\n" % (time, user, text)
		db.close()
		
		content = _get_partial_view("chat.html", { "messages":lines})
		_set_view(req, { "content":content})
	

def style(req):
	file = req.uri.split("/")[-1:][0]
	return _open_view(HOME+file)

def script(req):
	file = req.uri.split("/")[-1:][0]
	return _open_view(HOME+file)
	
def handler(self, req):
	pagebuffer = None
	SESSION = Session.Session(req)
	if not SESSION.has_key("user"):
		SESSION["user"] = "Anonym"
		SESSION.save()
		show_login(req)
	else:
		if(SESSION["user"] == "Anonym"):
			if (req.uri[:11] == '/registrace'):
				pagebuffer = register(req, '/registrace')
			elif (req.uri[:11] == '/prihlaseni' or req.uri == "/"):
				pagebuffer = login(req, '/prihlaseni')
		else:
		
			if (req.uri == '/index' or req.uri == '/'):
				pagebuffer = index(req)
			elif (req.uri[-4:] == '.css'):
				pagebuffer = style(req)
			elif (req.uri[-3:] == '.js'):
				pagebuffer = script(req)
			elif (req.uri[:5] == '/chat'):
				pagebuffer = chat(req, '/chat')
			elif (req.filename.split("/")[-2] == 'images'):
				req.content_type = "image/gif"
				req.sendfile(HOME+req.uri)
			else:
				#  use the contents of a file
				pagebuffer = req.uri
	
	pagebuffer=SESSION["user"]
	if(pagebuffer != None):
		req.write(pagebuffer)
	return(apache.OK)
