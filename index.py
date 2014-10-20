#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mod_python import apache, psp, Session, util
import cgi, MySQLdb, re
from time import localtime, strftime
import hashlib, binascii


HOME = "/home/tmpuser/Projects/Brandbook/"
LAYOUT = "layout.html"
DOMAIN = "http://193.19.178.168"
ADMIN_EMAIL = "brandbook@email.cz"
SESSION_USER = "user_id"


def GetDatabase():
	return MySQLdb.connect("localhost","root","Fv5p0bY28DqXq","brandbook")

def GetDatetime():
	return strftime("%Y-%m-%d %H:%M:%S", localtime())

def GetTime():
	time = strftime("%H:%M:%S", localtime())
	if time[0]=="0":
		return time[1:]
	else:
		return time

def GetFile(file):
	f = open(file, "r")
	view = f.read()
	f.close()
	return view

def GetHash(password, datetime):
	salt = datetime+"*mllkeúor.-§ǘ*"
	h = hashlib.new('sha1')
	h.update(password+salt)
	return h.hexdigest()

def IsValidEmail(email):
	return re.match(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', str(email)) != None
	
def EscapeHtmlSpecialChars(string):
	return cgi.escape(string, True).replace("'","&apos;")	

class Website(object):
	def __init__(self, req):
		self.req = req
		self.session = Session.Session(req)
		self.flashmessage = ""
	
	def show_part_view(self, file):
		layout = self._get_template(file).replace("req.write", "self.req.write").replace("flashmessage", "self.flashmessage")
				
		user_id = str(self.session[SESSION_USER])
		f = open(HOME+"rendering_page"+user_id , "w")
		f.write("# -*- coding: utf-8 -*-\n"+layout)
		f.close()
		
		exec open(HOME+"rendering_page"+user_id , "r")
	
	
	def _get_partial_view(self, file, model):
		content = GetFile(HOME+file)
		for key, value in model.iteritems():
			content = content.replace("<%="+key+"%>", value)
		return content

	def _set_view(self, model={}, layout=LAYOUT):
		tmpl = psp.PSP(self.req, layout)
		tmpl.run(vars = model, flush=False)
		
	def _get_template(self, file):
		return psp.parse(HOME+file)

class Page(Website):
	def __init__(self, page):
		self.req = page.req
		self.session = page.session
		self.flashmessage = page.flashmessage
		self.log = ""
		self.response = ""
	
	def show(self, layout):
		self._set_view({"flashmessage":self.flashmessage}, layout=layout)
	
	def __str__(self):
		if(self.log != ""):
			return self.log
		elif(self.response != ""):
			return self.response
		return ""
		
class Redirect():
	@staticmethod
	def registration(req):
		util.redirect(req, DOMAIN+Route.registration)
		
	@staticmethod
	def index(req):
		util.redirect(req, DOMAIN+Route.index)	
		
	@staticmethod
	def login(req):
		util.redirect(req, DOMAIN+Route.login)
	
	@staticmethod
	def chat(req):
		util.redirect(req, DOMAIN+Route.chat)
	
class Route():
	index = "/index"
	registration = "/registrace"
	login = "/prihlaseni"
	chat = "/chat"
	profile = "/profil"
	my_wall = "/moje-zed"
	public_wall = "/verejna-zed"
	members = "/clenove"
	logout = "/odhlaseni"
	
class Database():
	def __init__(self):
		self.db = GetDatabase()
		self.cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
		self.sql = ""
		
	def run_sql(self, sql=""):
		if(sql == ""):
			sql=self.sql
		else:
			self.sql = sql
		self.cursor.execute(self.sql)
	
	def fetchall(self):
		return self.cursor.fetchallDict()
	
	def _check_model(self, model):
		for key, value in model.iteritems():
			model[key] = EscapeHtmlSpecialChars(str(value))
		return model
	
	def _set_where(self, where):
		if where != {}:
			where = self._check_model(where)
			return "WHERE %s='%s'" % (where.keys()[0], where.values()[0])
		else:
			return ""
	
	def insert(self, model, table):
		model = self._check_model(model)
		keys = ", ".join(model.keys())
		values = "%s, " * len(model.values())
		values = values[:-2]
		
		self.sql = "INSERT INTO %s (%s) VALUES (%s);" % (table, keys, values)
		self.cursor.execute(self.sql, tuple(model.values()))
		self.db.commit()
			
	def update(self, model, table, where={}):
		model = self._check_model(model)
		set_values = ""
		for key, value in model.iteritems():
			set_values += "%s='%s', " % (key, value)
		set_values = set_values[:-2]
		where = self._set_where(where)
		
		self.sql = "UPDATE %s SET %s %s;" % (table, set_values, where)
		self.run_sql()
		self.db.commit()
		
	def select_one(self, rows, table, where={}):
		return self.select(rows, table, where)[0]
	
	def select(self, columns, table, where={}, order_type="asc", order_by=""):
		where = self._set_where(where)
		if order_by != "":
			order = "ORDER BY "+order_by+" "+order_type
		else:
			order = ""
		self.sql = "SELECT %s FROM %s %s %s;" % (", ".join(columns), table, where, order)
		self.cursor.execute(self.sql)
		self.db.commit()
		return self.cursor.fetchallDict()
	
	def join_select(self, columns1, columns2, table1, table2, where={}, order_type="asc", order_by=""):
		where = self._set_where(where)
		if order_by != "":
			order = "ORDER BY "+order_by+" "+order_type
		else:
			order = ""
		self.sql = """SELECT %s.%s, %s.%s
					FROM %s
					INNER JOIN %s
					ON %s.id=%s.user_id %s %s;""" % (table1,(", "+table1+".").join(columns1),table2, (", "+table2+".").join(columns2), table1, table2, table1, table2, where, order)
		#return self.sql
		self.cursor.execute(self.sql)
		self.db.commit()
		return self.cursor.fetchallDict()
		
	def set_sql(self, sql):
		self.sql = sql
	
	def get_sql(self):
		return self.sql
		
	def close(self):
		self.db.close()

class User():
	TABLE = "users"
	id = "id"
	nick = "nick"
	email = "email"
	password_hash = "password_hash"
	created = "created"
	name = "name"
	surname = "surname"
	
	@staticmethod
	def get_id(db, user_email):
		user = db.select_one((User.id,), User.TABLE, where={User.email:user_email})
		return user[User.id]
		
	@staticmethod
	def get_nick(db, user_id):
		user = db.select_one((User.nick,), User.TABLE, where={User.id:user_id})
		return user[User.nick]
		
	@staticmethod
	def get_columns():
		return (User.id, User.nick, User.email, User.password_hash, User.created, User.name, User.surname)
		
class Profile():
	TABLE = "profiles"
	user_id = "user_id"
	last_change = "last_change"
	user_profile = "user_profile"
	web = "web"
	job = "job"
	doing = "doing"
	story = "story"
	
	@staticmethod
	def get_columns():
		return (Profile.user_id, Profile.last_change, Profile.user_profile, Profile.web, Profile.job, Profile.doing, Profile.story)
		
class Message():
	TABLE = "chat_messages"
	user_id = "user_id"
	created = "created"
	message = "message"
	@staticmethod
	def get_columns():
		return (Message.user_id, Message.created, Message.message)
		
class WallMessage():
	TABLE = "wall_messages"
	id = "id"
	user_id = "user_id"
	created = "created"
	message = "message"
	@staticmethod
	def get_columns():
		return (WallMessage.id, WallMessage.user_id, WallMessage.created, WallMessage.message)

class WallComment():
	TABLE = "wall_comments"
	id = "id"
	wall_message_id = "wall_message_id"
	user_id = "user_id"
	created = "created"
	message = "message"
	@staticmethod
	def get_columns():
		return (WallMessage.id, WallMessage.user_id, WallMessage.created, WallMessage.message)
		

##########################################################

class Registration(Page):
	def __init__(self, page, root_uri=Route.registration):
		super(Registration,self).__init__(page)
		
		def parse_form():
			form = util.FieldStorage(self.req)
			self.email = form.getfirst("email")
			self.pass1 = form.getfirst("pass1")
			self.pass2 = form.getfirst("pass2")
		
		def validate():
			if not IsValidEmail(self.email):
				self.flashmessage += "Špatně zadaný email.<br/>"
			if (self.pass1 == None or len(self.pass1) < 6):
				self.flashmessage += "Heslo musí být dlouhé alespoň 6 znaků.<br/>"
			if (self.pass1 != self.pass2):
				self.flashmessage += "Hesla se musí shodovat.<br/>"
		
		def save_user_and_redirect():
			datetime = GetDatetime()
			def get_usermodel():
				model = {}
				model[User.nick] = self.email.split("@")[0]
				model[User.email] = self.email
				model[User.created] = datetime
				model[User.password_hash] = GetHash(self.pass1, datetime)
				return model
			try:	
				db = Database()
				db.insert(get_usermodel(), User.TABLE)
				user_id = User.get_id(db, self.email)
				db.insert( {Profile.user_id:user_id, Profile.last_change:datetime, Profile.story:' '}, Profile.TABLE)
				db.close()
			
				self.flashmessage += "Registrace proběhla úspěšně. Nyní se můžete přihlásit.<br/><br/>"
				login = Login(self)
				login.show()
			except Exception, ex:
				self.flashmessage += str(ex)+"<br/>Někde se stala nějaká neznámá chyba, <br/>kontaktujte admina: %s<br/><br/>" % ADMIN_EMAIL
				self.show()
		
		def run():
			if(self.req.uri == root_uri):
				self.show()
			elif(self.req.uri == root_uri+"_send"):
				parse_form()
				validate()
				if (self.flashmessage != ""):	
					self.show()
				else:
					save_user_and_redirect()
					
		run()
			
	def show(self):
		super(Registration,self).show("registration.html")
		
class Login(Page):
	def __init__(self, page, root_uri=Route.login):
		super(Login,self).__init__(page)
		self.user = None
		
		def parse_form():
			form = util.FieldStorage(self.req)
			self.email = form.getfirst("email")
			self.password = form.getfirst("password")
		
		def login():
			try:
				db = Database()
				columns = { User.id, User.email, User.password_hash, User.created }
				user = db.select_one(columns, User.TABLE, where={User.email:self.email})
				db.close()
				
				hash = GetHash(self.password, str(user[User.created]))
				if hash == user[User.password_hash]:
					self.user = user
					return True
				
				return False
			except Exception, ex:
				#self.flashmessage += str(ex)
				return False
			
		def try_login():
			if login():
				self.session[SESSION_USER] = self.user[User.id]
				self.session.save()
				Redirect.index(self.req)
			else:
				self.flashmessage += "Přihlášení proběhlo neúspěšně. Email nebo heslo není správně.<br/>"
				self.show()
		
		def run():
			if(self.req.uri == root_uri+"_send"):
				parse_form()
				try_login()
				
			elif(self.req.uri == root_uri):
				self.show()
				
		run()
		
	def show(self):
		super(Login,self).show("login.html")
	
class Logout(Page):
	def __init__(self, page, root_uri=Route.logout):
		super(Logout,self).__init__(page)
		self.session.delete()
		Redirect.login(self.req)	
		
class Index(Page):
	def __init__(self, page, root_uri=Route.index):
		super(Index,self).__init__(page)
		self.show()
		
	def show(self):
		content = self._get_partial_view("content.html", { "flashmessage":self.flashmessage})
		self._set_view({ "content":content})
		
class Chat(Page):
	def __init__(self, page, root_uri=Route.chat):
		super(Chat,self).__init__(page)
		
		def parse_form():
			form = util.FieldStorage(self.req)
			self.message = form.getfirst("message")
			self.last_update = form.getfirst("last_update")
			
		def save_message():
			try:
				db = Database()
				user_id = self.session[SESSION_USER]
				model = {}
				model[Message.user_id] = user_id
				model[Message.created] = GetTime()
				model[Message.message] = self.message				
				
				self.user_nick = User.get_nick(db, user_id)
				db.insert(model, Message.TABLE)
				
				db.close()
				return True
			except Exception, ex:
				return False
			
		def load_last_messages(num=15, in_time=None):
			where = {}
			if in_time != None:
				where = {Message.created:in_time}
				
			db = Database()
			messages = db.select(Message.get_columns(), Message.TABLE, where)[-num:]
			
			lines = ""
			for message in messages:
				user = db.select_one((User.nick,), User.TABLE, where={User.id:message[Message.user_id]})
				lines += "<b>[%s] %s:</b> %s <br/>\n" % (message[Message.created], user[User.nick], message[Message.message])
			db.close()
			return lines
			
		def run():	
			if (self.req.uri == root_uri+"/send_post"):
				parse_form()
				if save_message():
					self.response += ""
				else:
					self.response += "[%s] Chyba: Někde se stala nečekaná chyba.<br/>\n" % GetTime()
			
			elif (self.req.uri == root_uri+"/send_update"):
				parse_form()
				time = self.last_update
				second = int(time[-2:])
				time = time[:-2] + str(second-1)
				self.response += load_last_messages(in_time=time)
				
			elif(self.req.uri == root_uri):
				self.lines = load_last_messages()
				self.show()
		run()
		
	def show(self):
		content = self._get_partial_view("chat.html", { "messages":self.lines})
		self._set_view({ "content":content})
	
class ProfilePage(Page):
	def __init__(self, page, root_uri=Route.profile):
		super(ProfilePage,self).__init__(page)
		self.profile_form = {}
		
		def parse_form():
			form = util.FieldStorage(self.req)
			for key in form.keys():
				self.profile_form[key] = EscapeHtmlSpecialChars(form.getfirst(key).value)
		
		def save_profile():
			def is_in_profile():
				profile_form = {}
				for name, value in self.profile_form.iteritems():
					for column in Profile.get_columns():
						if name == column:
							profile_form[name] = value
							break
				return profile_form
			
			def is_in_user():
				profile_form = {}
				for name, value in self.profile_form.iteritems():
					for column in User.get_columns():
						if name == column:
							profile_form[name] = value
							break
				return profile_form
			
			try:
				self.profile_form[Profile.last_change] = GetDatetime()
				user_id = self.session[SESSION_USER]
				
				db = Database()
				profile_columns = is_in_profile()
				user_columns = is_in_user()
				
				if profile_columns != {}:
					where = {Profile.user_id:user_id}
					db.update(profile_columns, Profile.TABLE, where)
				if user_columns != {}:
					where = {User.id:user_id}
					db.update(user_columns, User.TABLE, where)
				db.close()
				
				return True
			except Exception, ex:
				#self.flashmessage += str(ex)+"<br/>" 
				return False
		
		def get_profile_data(user_id):
			db = Database()
			user_data = db.select_one(User.get_columns(), User.TABLE, {User.id:user_id})
			profile_data = db.select_one(Profile.get_columns(), Profile.TABLE, {Profile.user_id:user_id})
			profile_form = dict(user_data, **profile_data)
			db.close()
			return profile_form
		
		def run():
			if (self.req.uri == root_uri):
				try:
					form = util.FieldStorage(self.req)
					if form.has_key("user_id"):
						user_id = form.getfirst("user_id")
						self.profile_form = get_profile_data(user_id)
					else:
						self.profile_form = get_profile_data(self.session[SESSION_USER])
					self.show("profile.html")	
				except Exception, ex:
					self.response = "404"			
			elif (self.req.uri == root_uri+"_edit"):
				self.profile_form = get_profile_data(self.session[SESSION_USER])
				self.show("profile_edit.html")
			elif (self.req.uri == root_uri+"_send"):
				parse_form()
				self.profile_form[User.id] = self.session[SESSION_USER]
				if(save_profile()):
					self.flashmessage += "Profil byl úspěšně aktualizován."
				else:
					self.flashmessage += "Během ukládání se stala nečekaná chyba."
				self.show("profile.html")
				
		run()
			
	def show(self, file):
		content = self._get_template(file)
		user_id = str(self.session[SESSION_USER])
		layout = self._get_template(LAYOUT)
		layout = layout.replace("req.write(str(content),0);", content[:-1]+";").replace("req.write", "self.req.write").replace("flashmessage", "self.flashmessage")
		
		f = open(HOME+"rendering/rendering_page"+user_id , "w")
		f.write("# -*- coding: utf-8 -*-\n"+layout)
		f.close()
		
		exec open(HOME+"rendering/rendering_page"+user_id , "r")
		#self._set_view({ "content":content, "flashmessage":self.flashmessage})
		
class MyWall(Page):
	def __init__(self, page, root_uri=Route.my_wall):
		super(MyWall,self).__init__(page)
		self.message = None
		self.model = None
		self.title = "Moje zeď"
		self.limit_messages = 10
		self.root_uri = root_uri
		
		def parse_form():
			form = util.FieldStorage(self.req)
			self.message = form.getfirst("contribution")
			if form.has_key("page"):
				self.page = int(form.getfirst("page"))
		
		def parse_comment_form():
			form = util.FieldStorage(self.req)
			self.message_id = str(form.getfirst("message_id"))
			self.comment = form.getfirst("comment_message")
		
		def save_comment():
			model = {}
			model[WallComment.wall_message_id] = self.message_id
			model[WallComment.created] = GetDatetime()
			model[WallComment.user_id] = self.session[SESSION_USER]
			model[WallComment.message] = self.comment
			
			db = Database()
			db.insert(model, WallComment.TABLE)
			db.close()	
		
		def save_message():
			model = {}
			model[WallMessage.message] = self.message
			model[WallMessage.user_id] = self.session[SESSION_USER]
			model[WallMessage.created] = GetDatetime()
			
			db = Database()
			db.insert(model, WallMessage.TABLE)
			db.close()
		
		def get_messages(from_num, to_num):
			columns1 = (User.id+" as user_id", User.name, User.surname, User.email)
			columns2 = (WallMessage.id, WallMessage.message, WallMessage.created)
			db = Database()
			model = db.join_select(columns1, columns2, User.TABLE, WallMessage.TABLE, where={User.TABLE+"."+User.id:self.session[SESSION_USER]}, order_type="desc", order_by=WallMessage.TABLE+"."+WallMessage.created)[from_num:to_num]
			for row in model:
				row["count_comments"] = db.select_one(("count(*)",), WallComment.TABLE, where={WallComment.wall_message_id:row[WallMessage.id]}).values()[0]
			db.close()
			return model
		
		def get_comments(from_num=0, to_num=10, limit=0, order_type="desc"):
			columns1 = (User.id+" as user_id", User.name, User.surname, User.email)
			columns2 = (WallComment.id, WallComment.message, WallComment.created)
			db = Database()
			model = db.join_select(columns1, columns2, User.TABLE, WallComment.TABLE, where={WallComment.TABLE+"."+WallComment.wall_message_id:self.message_id}, order_type=order_type, order_by=WallComment.TABLE+"."+WallComment.created)[limit:]
			db.close()
			return model
		
		def run():
			if (self.req.uri == Route.my_wall):
				self.model = get_messages(0, self.limit_messages)
				self.show("wall.html")
			elif (self.req.uri == Route.my_wall+"_send"):
				parse_form()
				save_message()
				self.model = get_messages(0, self.limit_messages)
				self.flashmessage += "Příspěvek byl přidán."
				self.show("wall.html")
			elif (self.req.uri == Route.my_wall+"/next_messages"):
				parse_form()
				from_num = self.limit_messages*self.page
				self.model = get_messages(from_num, from_num+self.limit_messages)
				self.show_part_view("wall_messages.html")
			elif (self.req.uri == root_uri+"/send_comment"):
				parse_comment_form()
				save_comment()
				self.model = get_comments(limit=-1, order_type="asc")
				self.show_part_view("wall_comments.html")
			
			elif (self.req.uri == root_uri+"/show_comments"):
				parse_comment_form()
				self.model = get_comments(order_type="asc")
				self.show_part_view("wall_comments.html")
		run()
	
	def show(self, file):
		content = self._get_template(file)
		user_id = str(self.session[SESSION_USER])
		layout = self._get_template(LAYOUT)
		layout = layout.replace("req.write(str(content),0);", content[:-1]+";").replace("req.write", "self.req.write").replace("flashmessage", "self.flashmessage")
		
		f = open(HOME+"rendering/rendering_page"+user_id , "w")
		f.write("# -*- coding: utf-8 -*-\n"+layout)
		f.close()
		
		exec open(HOME+"rendering/rendering_page"+user_id , "r")
	
class PublicWall(Page):
	def __init__(self, page, root_uri=Route.public_wall):
		super(PublicWall,self).__init__(page)
		self.message = None
		self.model = None
		self.title = "Veřejná zeď"
		self.limit_messages = 10
		self.root_uri = root_uri
		
		def parse_form():
			form = util.FieldStorage(self.req)
			self.message = form.getfirst("contribution")
			if form.has_key("page"):
				self.page = int(form.getfirst("page"))
		
		def parse_comment_form():
			form = util.FieldStorage(self.req)
			self.message_id = str(form.getfirst("message_id"))
			self.comment = form.getfirst("comment_message")
		
		def save_comment():
			model = {}
			model[WallComment.wall_message_id] = self.message_id
			model[WallComment.created] = GetDatetime()
			model[WallComment.user_id] = self.session[SESSION_USER]
			model[WallComment.message] = self.comment
			
			db = Database()
			db.insert(model, WallComment.TABLE)
			db.close()	
		
		def save_message():
			model = {}
			model[WallMessage.message] = self.message
			model[WallMessage.user_id] = self.session[SESSION_USER]
			model[WallMessage.created] = GetDatetime()
			
			db = Database()
			db.insert(model, WallMessage.TABLE)
			db.close()
		
		def get_messages(from_num=0, to_num=10):
			columns1 = (User.id+" as user_id", User.name, User.surname, User.email)
			columns2 = (WallMessage.id, WallMessage.message, WallMessage.created)
			db = Database()
			model = db.join_select(columns1, columns2, User.TABLE, WallMessage.TABLE, order_type="desc", order_by=WallMessage.TABLE+"."+WallMessage.created)[from_num:to_num]
			for row in model:
				row["count_comments"] = db.select_one(("count(*)",), WallComment.TABLE, where={WallComment.wall_message_id:row[WallMessage.id]}).values()[0]
			db.close()
			return model
		
		def get_comments(from_num=0, to_num=10, limit=0, order_type="desc"):
			columns1 = (User.id+" as user_id", User.name, User.surname, User.email)
			columns2 = (WallComment.id, WallComment.message, WallComment.created)
			db = Database()
			model = db.join_select(columns1, columns2, User.TABLE, WallComment.TABLE, where={WallComment.TABLE+"."+WallComment.wall_message_id:self.message_id}, order_type=order_type, order_by=WallComment.TABLE+"."+WallComment.created)[limit:]
			db.close()
			return model
		
		def run():
			if (self.req.uri == Route.public_wall):
				self.model = get_messages(0, self.limit_messages)
				self.show("wall.html")
			elif (self.req.uri == root_uri+"_send"):
				parse_form()
				save_message()
				self.model = get_messages(0, self.limit_messages)
				self.flashmessage += "Příspěvek byl přidán."
				self.show("wall.html")
			elif (self.req.uri == root_uri+"/next_messages"):
				parse_form()
				from_num = self.limit_messages*self.page
				self.model = get_messages(from_num, from_num+self.limit_messages)
				self.show_part_view("wall_messages.html")
			elif (self.req.uri == root_uri+"/send_comment"):
				parse_comment_form()
				save_comment()
				self.model = get_comments(limit=-1, order_type="asc")
				self.show_part_view("wall_comments.html")
			
			elif (self.req.uri == root_uri+"/show_comments"):
				parse_comment_form()
				self.model = get_comments(order_type="asc")
				self.show_part_view("wall_comments.html")
				
		run()
	

	def show(self, file):
		content = self._get_template(file)
		user_id = str(self.session[SESSION_USER])
		layout = self._get_template(LAYOUT)
		layout = layout.replace("req.write(str(content),0);", content[:-1]+";").replace("req.write", "self.req.write").replace("flashmessage", "self.flashmessage")
		
		f = open(HOME+"rendering/rendering_page"+user_id , "w")
		f.write("# -*- coding: utf-8 -*-\n"+layout)
		f.close()
		
		exec open(HOME+"rendering/rendering_page"+user_id , "r")

class Members(Page):
	def __init__(self, page, root_uri=Route.members):
		super(Members,self).__init__(page)
		db = Database()
		self.model = db.join_select(User.get_columns(), (Profile.user_profile, Profile.job, Profile.doing), User.TABLE, Profile.TABLE, order_by=User.name)
		db.close()
		self.show("members.html")
	def show(self, file):
		content = self._get_template(file)
		user_id = str(self.session[SESSION_USER])
		layout = self._get_template(LAYOUT)
		layout = layout.replace("req.write(str(content),0);", content[:-1]+";").replace("req.write", "self.req.write").replace("flashmessage", "self.flashmessage")
		
		f = open(HOME+"rendering/rendering_page"+user_id , "w")
		f.write("# -*- coding: utf-8 -*-\n"+layout)
		f.close()
		
		exec open(HOME+"rendering/rendering_page"+user_id , "r")

		
class Brandbook(Website):
	
	def __init__(self, req):
		super(Brandbook,self).__init__(req)
		self.session.set_timeout(60*60*15)
	
	def style(self):
		file = self.req.uri#.split("/")[-1:][0]
		return GetFile(HOME+file)

	def script(self):
		file = self.req.uri#.split("/")[-1:][0]
		return GetFile(HOME+file)
		
	def is_uri(self, uri):
		return (self.req.uri[:len(uri)] == uri)	
		
	def handler(self):
		pagebuffer = None
		if not self.session.has_key(SESSION_USER):
			self.session[SESSION_USER] = "Anonym"
			self.session.save()
			login = Login(self)
			login.show()
		else:
			if(self.session[SESSION_USER] == "Anonym"):
				if (self.is_uri(Route.registration)):
					pagebuffer = str(Registration(self, Route.registration))
				elif (self.is_uri(Route.login) or self.req.uri == "/"):
					pagebuffer = str(Login(self, Route.login))
				else:
					login = Login(self)
					login.show()
			else:
			
				if (self.is_uri(Route.index) or self.req.uri == '/' or self.req.uri == ''):
					pagebuffer = str(Index(self, Route.index))
				elif (self.is_uri(Route.chat)):
					pagebuffer = str(Chat(self, Route.chat))
				elif (self.is_uri(Route.profile)):
					pagebuffer = str(ProfilePage(self, Route.profile))
				elif (self.is_uri(Route.public_wall)):
					pagebuffer = str(PublicWall(self, Route.public_wall))
				elif (self.is_uri(Route.my_wall)):
					pagebuffer = str(MyWall(self, Route.my_wall))
				elif (self.is_uri(Route.members)):
					pagebuffer = str(Members(self, Route.members))
				elif (self.is_uri(Route.logout)):
					pagebuffer = str(Logout(self, Route.logout))
				
				elif (self.req.uri[-4:] == '.css'):
					pagebuffer = self.style()
				elif (self.req.uri[-3:] == '.js'):
					pagebuffer = self.script()
				elif (self.req.filename.split("/")[-2] == 'images'):
					self.req.content_type = "image/gif"
					self.req.sendfile(HOME+req.uri)
				else:
					pagebuffer = str(self.session.timeout())
		
		if(pagebuffer != None):
			self.req.write(pagebuffer)
		return(apache.OK)

def handler(req):
	try:
		page = Brandbook(req)
		return page.handler()
	except Exception, ex:
		pass

