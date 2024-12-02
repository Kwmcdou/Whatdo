# Whatdo

Prioritization product to help decide what to do.

## Project Setup

Follow the steps below to set up the project locally and start the Flask development server:

### Prerequisites

Ensure you have the following installed on your system:

- Python 3.11.5
- pip (Python package installer)

### Installation Steps

1. **Clone the Repository**

   Clone this repository to your local machine using:

   ```bash
   git clone https://github.com/your-username/whatdo.git
   cd whatdo
   ```

2. **Create a Virtual Environment**

   It's best practice to use a virtual environment to manage dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   Install the necessary Python packages specified in your requirements:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**

   If your application uses an SQLite database, ensure you set it up properly. The `whatdo.db` file should be initialized with the correct schema. You can use any provided SQL scripts or migration tools that come with your project to set it up.

5. **Environment Configuration**

   You may need to set environment variables for your Flask app to ensure it runs correctly. Create a `.env` file or set the variables directly in your shell:

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development  # Enables debug mode
   ```

   On Windows, you might use `set` instead:

   ```cmd
   set FLASK_APP=app.py
   set FLASK_ENV=development
   ```

### Running the Application

With everything set up, you can start the Flask development server using:

```bash
flask run
```

This command will launch your application, and you can access it by navigating to `http://localhost:5000` in your web browser.

### Troubleshooting

- Ensure your virtual environment is activated when you run the Flask command.
- Check your database initialization if the application fails to connect to the database.
- Review any Flask error messages displayed in the console for debugging tips.

### Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [CS50 Library Documentation](https://cs50.readthedocs.io/)