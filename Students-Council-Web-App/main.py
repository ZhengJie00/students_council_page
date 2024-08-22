import csv
import sqlite3
from flask import Flask, render_template, redirect, request, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'secret_key_101'

def account_check(username, password):
    """Check if the username and password exist in the CSV file."""
    with open('accounts.csv', 'r') as file:
        csv_reader = csv.reader(file)
        # Skip header row if present
        next(csv_reader)
        for row in csv_reader:
            if row[1] == username.upper() and row[2] == password:
                try:
                    session['role'] = row[3]
                    session['id'] = row[0]
                except IndexError:
                    session['role'] = None
                    session['id'] = row[0]
                return True
    return False

def create_table():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Task (
        stu_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        status TEXT NOT NULL,
        PRIMARY KEY (stu_id, task)
    )
    """)

    # Insert tasks if they do not already exist
    tasks = [('Plan for Orientation', 'Incomplete')] * 32
    cursor.executemany("""
    INSERT OR IGNORE INTO Task (stu_id, task, status)
    VALUES (?, ?, ?)
    """, [(i+1, task, status) for i, (task, status) in enumerate(tasks)])

    conn.commit()
    conn.close()

# app routes
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].upper()
        password = request.form['password']

        if account_check(username, password):
            session['username'] = username.title()  # Save username in session
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/council_events', methods=['GET'])
def council_events():
    return render_template('council_events.html')

@app.route('/roles_and_responsibilities', methods=['GET'])
def roles_and_responsibilities():
    return render_template('roles_and_responsibilities.html')

@app.route('/task_tracker', methods=['GET', 'POST'])
def task_tracker():
    create_table()
    
    if request.method == 'POST':
        new_task = request.form.get('new_task')
        status = request.form.get('status')
        existing_task = request.form.get('existing_task')
        updated_status = request.form.get('updated_status')
        delete_task = request.form.get('delete_task')

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        if new_task and status:
            cursor.execute("SELECT task FROM Task WHERE stu_id = ?", (session['id'],))
            tasks = cursor.fetchall()
            if (new_task not in [task[0] for task in tasks]) and (status.title() in ['Completed', 'Incomplete']):
                cursor.execute("""
                INSERT INTO Task (stu_id, task, status)
                VALUES(?, ?, ?)
                """, (session['id'], new_task, status))
                conn.commit()
            else:
                flash('Task already exists or status is invalid.')

        if existing_task and updated_status:
            if updated_status.title() in ['Completed', 'Incomplete']:
                cursor.execute("""
                UPDATE Task SET status = ? WHERE stu_id = ? AND task = ?
                """, (updated_status.title(), session['id'], existing_task))
                conn.commit()
            else:
                flash('Status is invalid.')

        if delete_task:
            cursor.execute("""
            DELETE FROM Task WHERE stu_id = ? AND task = ?
            """, (session['id'], delete_task))
            conn.commit()

        conn.close()

    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    completed_tasks = cursor.execute("SELECT task FROM Task WHERE stu_id = ? AND status = 'Completed'", (session['id'],)).fetchall()
    incomplete_tasks = cursor.execute("SELECT task FROM Task WHERE stu_id = ? AND status = 'Incomplete'", (session['id'],)).fetchall()

    try:
        percentage_completed = len(completed_tasks) / (len(completed_tasks) + len(incomplete_tasks)) * 100
        task_percentage = f"{percentage_completed:.2f}%"
    except ZeroDivisionError:
        task_percentage = "0%"

    conn.close()

    return render_template('task_tracker.html', completed_tasks=completed_tasks, incomplete_tasks=incomplete_tasks, task_percentage=task_percentage, percentage_completed=percentage_completed)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
