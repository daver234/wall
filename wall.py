from flask import Flask, request, redirect, render_template, session, flash
import unicodedata
import re
from flask.ext.bcrypt import Bcrypt
from mysqlconnection import MySQLConnector
app = Flask(__name__)

bcrypt = Bcrypt(app)
mysql = MySQLConnector('walldb')


app.secret_key = '(\xa6()\xa7\x81kB$l\t\xed\x19\x95e:\x82\xc6-\xac\xb1Z\xe3*' 

@app.route('/')
def index():
  return render_template("index.html")


@app.route('/reg', methods=['POST'])
def create_user():
	EMAIL_REGEX = re.compile(r'^[a-za-z0-9\.\+_-]+@[a-za-z0-9\._-]+\.[a-za-z]*$')
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	email = request.form['email']
	password = request.form['password']
	pw_confirmation = request.form['pw_confirmation']
	error_count = 0
	#first name validations
	if not first_name:
	    flash(u'First Name cannot be blank', 'regis_errors')
	    error_count += 1
	elif not first_name.isalpha():
	    flash(u'First Name must contain valid characters', 'regis_errors')
	    error_count += 1
	elif len(first_name) < 3:
	    flash(u'First Name cannot be less than 3 characters', 'regis_errors')
	    error_count += 1
	#last name validations
	if not last_name:
	    flash(u'Last Name cannot be blank', 'regis_errors')
	    error_count += 1
	elif not last_name.isalpha():
	    flash(u'Last Name must contain valid characters', 'regis_errors')
	    error_count += 1
	elif len(last_name) < 3:
	    flash(u'Last Name cannot be less than 3 characters', 'regis_errors')
	    error_count += 1
	# email validations
	if not email:
	    flash(u'Email cannot be blank', 'regis_errors')
	    error_count += 1
	elif not EMAIL_REGEX.match(email):
	    flash(u'Email format must be valid', 'regis_errors')
	    error_count += 1
	# password validations
	if not password:
	    flash(u'Password cannot be blank', 'regis_errors')
	    error_count += 1
	if not pw_confirmation:
	    flash(u'Password Confirmation cannot be blank', 'regis_errors')
	    error_count += 1
	if password != pw_confirmation:
	    flash(u'Password Confirmation must match Password', 'regis_errors')
	    error_count += 1
	# if validations pass
	if error_count == 0:
	   # check if the user exists
	   exists_query = "SELECT * FROM users WHERE email = '{}'".format(email)
	   user = mysql.fetch(exists_query)
	   # if the user does not exist
	   if not user:
	        #we'll use bcrypt to create a hashed password
	        pw_hash = bcrypt.generate_password_hash(password)
	        # write the query to insert the user and then insert the user into the database
	        query = "INSERT INTO users (first_name, last_name, email, pw_hash, created_at, updated_at) VALUES ('{}','{}','{}','{}',NOW(),NOW())".format(first_name, last_name, email, pw_hash)
	        mysql.run_mysql_query(query)
	        # we'll then grab the user information from the db
	        user_query = "SELECT * FROM users ORDER BY id DESC LIMIT 1"
	        user = mysql.fetch(user_query)
	        # set the user id and first name in session
	        session['user_id'] = user[0]['id']
	        session['first_name'] = user[0]['first_name']
	        # set a flash messaged to display on the success page
	        flash(u'Successfully registered user!', 'success')
	        return redirect('/success')
	   else:
	        # if the user already exists we'll create a message to display in flash
	        flash(u'Email taken, please enter unique email address', 'regis_errors')
	# if we don't redirect to the success page, redirect back to the default route
	return redirect('/')


@app.route('/login', methods=['POST'])
def loginaccount():

	print "I am in /login now"
	# post info
	email = request.form['email']
	password = request.form['password']
	if email and password:
	    # find the user by their email
	    query = "SELECT * FROM users WHERE email = '{}'".format(email)
	    # retrieve from the database
	    user = mysql.fetch(query)
	    print user
	    # if we retrieved a user successfully and their password checks out
	    if user and bcrypt.check_password_hash(user[0]['pw_hash'], password):
	        # clear the session
	        session.clear()
	        # put the user's info into seession
	        session['user_id'] = user[0]['id']
	        session['first_name'] = user[0]['first_name']
	        flash(u'Successfully logged in user!', 'success')
	        return redirect('/wall')
	# in all other cases set the flash message and redirect to the index
	flash(u'Invalid login credentials', 'login_errors')
	
	return redirect('/wall') 


@app.route('/wall')
def thewall():

	print "I am now in /wall"
	id = session['user_id']
	print "user_id in /wall before query",id
	query = "SELECT users.first_name, users.last_name, messages.message, messages.created_at, messages.id FROM users LEFT JOIN messages on users.id = messages.users_id" #where users.id = '{}'".format(id)
	theperson = mysql.fetch(query)
	
	querymore = "SELECT users.first_name, users.last_name, comments.comment, comments.created_at, comments.messages_id FROM users LEFT JOIN comments ON users.id = comments.users_id"
	
	pcomments = mysql.fetch(querymore)

	print "the messages are: ", pcomments
	return render_template('wall.html', theperson=theperson, pcomments=pcomments)


@app.route('/logoff')
def logging_off():
	session.clear()
	return redirect('/')



@app.route('/postmessage/<message2>', methods=['POST'])
def post_message(message2):

	print "I am now in /postmessage"
	id = 0
	id = session['user_id']
	print "here is the user_id",session['user_id']

	posted = request.form['postex']
	print "here is the postmessage:",posted
	
	print "****************************"
	query3 ="INSERT INTO messages (users_id, message, created_at, udpated_at) VALUES ('{}', '{}', NOW(), NOW())".format(id,posted)
	mysql.run_mysql_query(query3)
	return redirect('/wall')


@app.route('/comment', methods=['POST'])
def post_comment():

	print "I am now in /postcoment"
	#id = 0
	id = session['user_id']
	print "here is the user_id",session['user_id']

	comment = request.form['commentex']
	print "here is the commentex:",comment

	message_id=request.form['message_id']
	print "Here is the message_id",message_id

	
	print "****************************"
	query4 ="INSERT INTO comments (messages_id, comment, users_id, created_at, updated_at) VALUES ('{}', '{}', '{}', NOW(), NOW())".format(message_id,comment, id)
	mysql.run_mysql_query(query4)
	return redirect('/wall')


@app.route('/show')
def showing():
	return redirect('/reset') 

@app.route('/success')	
def success():
	print "I'm in success.html"
	return render_template('success.html') 




@app.route('/reset')	
def clear_all():
	
	
	return redirect('/')

app.run(debug=True)