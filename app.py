import matplotlib
import matplotlib.dates as mdates
matplotlib.use('Agg')
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request, flash 
from forms import HabitForm
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd 
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.now)
    habit = db.relationship('Habit', backref=db.backref('logs', lazy=True))

    def __repr__(self):
        return f'<HabitLog habit_id={self.habit_id} at {self.completed_at}>'

with app.app_context():
    db.create_all()

@app.route('/', methods=["GET", "POST"])
def home():
    form = HabitForm()
    for habit in Habit.query.all():
        if habit.last_completed_at and habit.last_completed_at.date() < date.today():
            habit.completed = False
    db.session.commit()
    if form.validate_on_submit():
        new_habit = Habit(name=form.name.data)
        db.session.add(new_habit)
        db.session.commit()
        return redirect(url_for('home'))

    all_habits = Habit.query.all()
    completed_habits = Habit.query.filter_by(completed=True).all() 
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    habits_today = Habit.query.filter(
        Habit.created_at >= today_start,
        Habit.created_at <= today_end,
        Habit.completed == False
    ).order_by(Habit.created_at.desc()).all()

    return render_template('index.html', form=form, habits=all_habits, completed_habits=completed_habits, habits_today=habits_today)

@app.route('/toggle/<int:habit_id>', methods=["POST"])
def toggle_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.completed = 'completed' in request.form
    if habit.completed:
        log = HabitLog(habit_id=habit.id)
        db.session.add(log)
        flash('You successfully completed a habit!', 'success')
    else:
        flash('Habit marked as incomplete.', 'info')

    habit.last_completed_at = datetime.now()
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/one_habit_plot/<int:habit_id>')
def single_graph(habit_id):
    habit = db.get_or_404(Habit, habit_id)
    logs = HabitLog.query.filter_by(habit_id=habit.id).all()

    if not logs:
        flash("No completion data to plot yet.", "info")
        return redirect(url_for('home'))

    data = [{'Completed': 1, 'Date': log.completed_at.date()} for log in logs]
    df = pd.DataFrame(data)
    summary = df.groupby('Date').sum().reset_index()
    summary["Date"] = pd.to_datetime(summary["Date"])

    sns.barplot(x="Date", y="Completed", data=summary, width=0.3)
    plt.title(f"Habit: {habit.name}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join('static', 'images', f'habit_{habit.id}_plot.png')
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    plt.close()

    relative_path = plot_path.split("static/")[-1]
    return render_template('plot.html', plot_url=url_for('static', filename=relative_path))



@app.route('/habit_plot')
def habit_plot():
    logs = HabitLog.query.all()

    if not logs:
        flash("No completion data available yet.", "info")
        return redirect(url_for('home'))

    data = [{'Completed': 1, 'Date': log.completed_at.date()} for log in logs]
    df = pd.DataFrame(data)
    summary = df.groupby('Date').sum().reset_index()
    summary["Date"] = pd.to_datetime(summary["Date"])

    sns.barplot(x="Date", y="Completed", data=summary, width=0.3)
    plt.title("All Habit Completions by Day")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join('static', 'images', 'all_habit_plot.png')
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    plt.close()

    relative_path = plot_path.split("static/")[-1]
    return render_template('plot.html', plot_url=url_for('static', filename=relative_path))



@app.route("/edit-habit/<int:habit_id>", methods=["GET", "POST"])
def edit_habit(habit_id):
    habit = db.get_or_404(Habit, habit_id)
    edit_form = HabitForm(name=habit.name)

    if edit_form.validate_on_submit():
        habit.name = edit_form.name.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit_habit.html", form=edit_form, is_edit=True, habit=habit)


@app.route("/delete_habit/<int:habit_id>", methods=["POST"])
def delete_habit(habit_id):
    habit_listed = db.session.get(Habit, habit_id)
    if habit_listed:
        db.session.delete(habit_listed)
        db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
