# DESIGN.md

## Project Overview

This project is a web application developed using the Flask framework that centers around event management, specifically enabling users to create, manage, and prioritize events and associated tasks (cards) to help them decide what to do next, WhatDo.

I chose to use of Flask and SQLite for database management not only to ensure a lightweight and efficient storage solution, but because it was familiar to me from the CS50 Finance project. CS50 is my first foray into computer science and coding. I considered using something like React and Tailwind which I believe would have been fun and interesting, but I don't think I would have been able to get as far as I have in the time constraints while trying to learn them for the first time.

## Architecture

### Application Framework

The application is built with Flask, a lightweight WSGI web application framework. Flask's modularity allows for easy code organization and the inclusion of various extensions for different functionalities. In this project, Flask extensions like `Werkzeug` for security and `Flask-Session` for managing user sessions are utilized.

### Database

The application uses the CS50 library for interfacing with an SQLite database. SQLite serves as an excellent choice due to its serverless nature, ease of use, and reliable performance for applications that don't require an extensive database server.

Tables include:

- **users**: for storing user credentials and related information like hashed passwords.
- **events**: capturing event details, such as event names and descriptive prompts.
- **user_events**: linking users with their respective events to manage permissions.
- **cards**: for managing tasks under specific events with priorities.

The schema includes fields for multiple prompts and linking users to events so that the project is able to be extended to include custom events and multiple users participating in an event in the future. 

### Security

Security is critical, especially for user authentication and session management. This was adapted from the Finance project to ensure it was functioning and to reduce the risk profile of this project:

- Passwords are hashed using Werkzeug's robust `generate_password_hash` and `check_password_hash` functionalities.
- Sessions use Flask-Session and are configured to use the filesystem rather than cookies for enhanced security.

### Routing and Views

Flask's routing capabilities direct traffic through clear, RESTful routes, enabling smooth navigation and resource access.

#### Key Routes and Logic

- **`/login`, `/logout`, `/register`**: These routes handle user authentication and account management features, ensuring secure user access.
  
- **Home Page (`/`)**: Displays user's events. It is the main entry point and is protected by a login requirement.

- **Event Management**: 
  - **`/create_event`**: Allows users to create new events, requiring an event name and a default prompt to guide card creation.
  - **`/view_event/<event_id>`** and **`/event/<event_id>`**: Display events and their associated cards, ensuring appropriate user permissions. They also separate concerns from editing or adding to an event and simply viewing the results of an event. 
  - **`/create_card`**: Provides functionality for users to add new cards (tasks) under an event.

- **Priority Management**:
  - **`/start_comparison`**, **`/submit_comparison`**: Handle task prioritization logic using card comparisons, ensuring distinct priority settings.

### Design Choices and Rationale

- **Flask Framework**: Chosen for its lightweight nature, ease of use, and robust community support, making it suitable for rapid development cycles.
  
- **SQLite Database**: Selected due to its simplicity, which aligns with the application's requirement for a straightforward, embedded database system.

- **Security**: Integrated best practices like hashing and session management to ensure user data integrity and privacy.

- **Session Management**: Opted for `Flask-Session` over signed cookies to benefit from its flexibility and the ability to store session data server-side.

In summary, the project's design up to this point focuses on a seamless user experience, maintaining security and efficiency in managing and prioritizing one type of event, a todo list. This setup allows me to test the workflow and get feedback from users while iterating on other event ideas and further features before expanding into a more complex database system.