from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import joblib
import numpy as np
import uuid


# Load the trained machine learning model
model = joblib.load('model.pkl')

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loan_applications.db'

# Initialize SQLAlchemy instance
db = SQLAlchemy(app)


# Define loan application model
class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def __init__(self, application_number, name, amount):
        self.application_number = application_number
        self.name = name
        self.amount = amount

# Create loan_applications table if it doesn't exist
with app.app_context():
    db.create_all()

# Define a route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Define a route for form submission
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Retrieve form data
        name = request.form['name']
        amount = float(request.form['amount'])

        # Make prediction using the machine learning model
        prediction = model.predict([[amount]])[0]

        if prediction == 1:
            # Generate a UUID for the loan application
            application_number = str(uuid.uuid4())

            # Store the data in the database
            save_loan_application(name, amount, application_number)

            # Return the prediction result and application number
            return render_template('success.html', prediction="Accepted", application_number=application_number, name=name)

        # Return the prediction result without the application number
        return render_template('success.html', prediction="Rejected", name=name)

    except (KeyError, ValueError) as e:
        error_message = str(e)
        return render_template('error.html', error_message=error_message)

    except Exception as e:
        error_message = "An error occurred while processing your request."
        # Log the error for debugging purposes
        print("Error:", str(e))
        return render_template('error.html', error_message=error_message)



# Save the loan application data to the database and return the application number
def save_loan_application(name, amount,application_number):
    # Generate a unique application number

    # Create a new LoanApplication object
    loan_application = LoanApplication(application_number=application_number, name=name, amount=amount)

    # Add the loan application to the database session
    db.session.add(loan_application)

    # Commit the changes to the database
    db.session.commit()

    return application_number

# Define a route for authentication
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'secret':  # Replace 'your_password' with the actual password
            return redirect('/data')
        else:
            error_message = 'Invalid password. Access denied.'
            return render_template('auth.html', error_message=error_message)
    return render_template('auth.html')

# Define a route to display all loan application data
@app.route('/data', methods=['POST'])
def data():
    loan_applications = LoanApplication.query.all()
    return render_template('applications.html', loan_applications=loan_applications)


# Handle 404 errors (Page not found)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message='Page not found'), 404

# Handle 500 errors (Internal server error)
@app.errorhandler(500)
def internal_error(error):
    # Log the error for debugging purposes
    print("Error:", str(error))
    return render_template('error.html', error_message='Internal server error'), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
