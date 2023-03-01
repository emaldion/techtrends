import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys
from datetime import datetime

# connection count metric
conn_count = 0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global conn_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    conn_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      log_message('Article with ID="{id}" Does Not Exist!'.format(id=post_id), 1)
      return render_template('404.html'), 404
    else:
      log_message('Article T="{title}" Successfully Retrieved!'.format(title=post['title']), 0)
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log_message('About Page Retrieved!', 0)
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            log_message('New Article T="{title}" Created!'.format(title=title), 0)

            return redirect(url_for('index'))

    return render_template('create.html')

# Define the /healthz endpoint for app best practices
@app.route('/healthz')
def healthz():

    connection = get_db_connection()

    connection.cursor()
    connection.execute("SELECT * FROM posts")
    connection.close()
    
    result = {"HTTP/1": 200, "result": "Ok - healthy"}

    return result


# Define /metrics endpoint for app best practices
@app.route("/metrics")
def metrics():
    try:
        connection = get_db_connection()

        posts = connection.execute("SELECT * FROM posts").fetchall()
        connection.close()
        posts_count = len(posts)
        
        status_code = 200

        addition = {"db_connection_count": conn_count, "post_count": posts_count}

        result = {"HTTP/1": status_code, "responce": addition}

        return result

    except Exception:       
        return {"result": "ERROR - Metrics"}, 500



# Log function handler
def log_message(msg, source):
    if source == 0:
        sys.stdout.write('{time} | {message} \n'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))
        app.logger.info('{time} | {message}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))
        print('{time} | {message}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))

    if source == 1:
        sys.stderr.write('{time} | {message} \n'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))
        app.logger.error('{time} | {message}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))
        print('{time} | {message}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))

# start the application on port 3111
if __name__ == "__main__":
    ## set log level to debug
    logging.basicConfig(level=logging.DEBUG)

    app.run(host='0.0.0.0', port='3111')

