Remote Laboratory Access and Scheduling Platform

This project is a desktop application for managing university laboratory reservations and simulated experiments. Students can create reservations, access experiments during their reserved time, save experiment results, and view their history. Administrators can manage users, equipment, reservations, and student lab time.

Requirements

Python 3

PyQt6

Matplotlib

Werkzeug

Running the Program

Run the program using:

python main.py

The application will automatically create the required database and load the available experiments.

Default Administrator Account

Username: admin

Password: Admin123

Basic Use

Create a student account from the login screen or log in using an existing account. Students can use the dashboard to manage reservations, run experiments during an active reservation, and view saved results.

Administrators can log in using an administrator account and open the Administrator Tools to manage the system.

The application stores its data in a local SQLite database.