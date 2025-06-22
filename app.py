import matplotlib
import matplotlib.dates as mdates
matplotlib.use('Agg')  # Use non-GUI backend
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request, flash 
from forms import HabitForm
from forms import Checked_Off
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd 
import os

app = Flask(__name__)

# SQLite Database Configuration
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
    completed_habits= Habit.query.filter_by(completed = True).all() 
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    habits_today = Habit.query.filter(
    Habit.created_at >= today_start,
    Habit.created_at <= today_end, Habit.completed == False
    ).order_by(Habit.created_at.desc()).all()
    return render_template('index.html', form=form, habits=all_habits, completed_habits=completed_habits, habits_today=habits_today)



###toogle habit #####
@app.route('/toggle/<int:habit_id>', methods=["POST"])
def toggle_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.completed = 'completed' in request.form
    if habit.completed:
        flash('You successfully completed a habit!', 'success')
    else:
        flash('Habit marked as incomplete.', 'info')

    previous_completion = habit.last_completed_at

    #reward
    if previous_completion and datetime.now() - previous_completion > timedelta(days=2):
        print("It's been more than 2 days!")

    # Now update it
    habit.last_completed_at = datetime.now()

    if previous_completion and datetime.now() - previous_completion < timedelta(days=2):
        print("You haven't practiced this habit for over 2 days")

    db.session.commit()
    return redirect(url_for('home'))




# plot one habit 
@app.route('/one_habit_plot/<int:habit_id>')
def single_graph(habit_id):
    habit = db.get_or_404(Habit, habit_id)
    data_one = [{'Completed': habit.completed, 'Date': habit.last_completed_at}]
    df = pd.DataFrame(data_one)
    df['Completed'] = df['Completed'].astype(int)
    summary = df.groupby('Date').sum().reset_index()
    
     ##Plotting###
    sns.lineplot(x="Date", y="Completed", data=summary, marker="o")
    summary['Date'] = summary['Date'].dt.strftime('%Y-%m-%d %I:%M %p')
    sns.barplot(x="Date", y="Completed", data=summary, width=0.2)
    plt.title(f"{habit_id} tracked")
    # Save the plot to the static directory
    plot_path = os.path.join('static', 'images', 'df_one_habit_one.png')
    plt.savefig(plot_path)

    plt.xticks(rotation=45)
    plt.tight_layout()

    return render_template('plot.html', plot_url=plot_path)


###all habit plots #####
@app.route('/habit_plot')  
def habit_plot():

    all_habits = Habit.query.filter(Habit.completed == True, Habit.last_completed_at != None).all()
    data = [{'Completed': h.completed, 'Date': h.last_completed_at} for h in all_habits]
    df = pd.DataFrame(data)
    df['Completed'] = df['Completed'].astype(int)
    summary = df.groupby('Date').sum().reset_index()

    ##Plotting###
    sns.lineplot(x="Date", y="Completed", data=summary, marker="o")
    summary['Date'] = summary['Date'].dt.strftime('%Y-%m-%d %I:%M %p')

    sns.barplot(x="Date", y="Completed", data=summary, width=0.2)
    plt.title("Daily Habit Completions")
    # Save the plot to the static directory
    plot_path = os.path.join('static', 'images', 'df_habits.png')
    plt.savefig(plot_path)
    plt.close() # Close the plot to free memory

 
    plt.xticks(rotation=45)
    plt.tight_layout()

    return render_template('plot.html', plot_url=plot_path)




####edit habit###
@app.route("/edit-habit/<int:habit_id>", methods=["GET", "POST"])
def edit_habit(habit_id):
    habit = db.get_or_404(Habit, habit_id)
    edit_form = HabitForm(name=habit.name)

    if edit_form.validate_on_submit():
        habit.name = edit_form.name.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit_habit.html", form=edit_form, is_edit=True, habit=habit)





####delete habit####
@app.route("/delete_habit/<int:habit_id>", methods=["POST"])
def delete_habit(habit_id):
    habit_listed = db.session.get(Habit, habit_id)
    if habit_listed:
        db.session.delete(habit_listed)
        db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
