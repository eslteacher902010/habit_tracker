A simple web app that lets you create, track, and visualize daily habits. Built with Flask, SQLAlchemy, and Matplotlib, deployed via Render.
Check it out here: https://habit-tracker-oc6k.onrender.com 

##Features:
- Add and delete habits
- Toggle completion status
- Track individual or all habits over time with bar graphs
- Save data using SQLite
- Flash messaging with Bootstrap


##Set up locally: 

1. Clone the repo:
```bash
git clone https://github.com/eslteacher902010/habit_tracker.git
cd habit_tracker

Create a virtual environment

python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

##Install requirements

pip install -r requirements.txt

##Run it

flask run


