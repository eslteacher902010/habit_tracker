# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class HabitForm(FlaskForm):
    name = StringField('Habit Name', validators=[DataRequired()])
    submit = SubmitField('Add Habit')


class Checked_Off(FlaskForm):
    power_switch = SubmitField("ON")