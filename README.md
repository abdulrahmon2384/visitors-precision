# Intelleva - Visitor Intelligence Platform

This is a web application built with Python and Flask that provides a live dashboard to track website visitors in real-time. It is designed to be a lightweight, single-file application for easy deployment and management.

## Features

*   **Live Visitor Dashboard:** View a comprehensive list of all visitors, updated in real time.
*   **Detailed Visitor Tracking:** Captures a wide range of data points, including:
    *   IP Address & Estimated Location
    *   Precise GPS Location (with user consent)
    *   Device Information (User Agent, Screen Resolution, etc.)
    *   Browser Capabilities (Plugins, Language, etc.)
*   **Dynamic Homepage Customization:** A settings panel on the dashboard allows you to change the homepage's welcome message, button text, and notification content without touching the code.
*   **Data Management:** Easily delete individual visitor records directly from the dashboard.
*   **Modern UI:** Features a clean, animated, and responsive user interface.

## Tech Stack

*   **Backend:** Python 3, Flask
*   **Database:** SQLite 3
*   **Frontend:** HTML, CSS, vanilla JavaScript

## Getting Started

### Prerequisites

*   Python 3
*   A virtual environment is recommended.

### Installation & Running the App

1.  **Activate the virtual environment:**
    This project is configured to work with a Nix environment. If you are in the intended workspace, a virtual environment is already created at `.venv`. Activate it with:
    ```bash
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    All required Python packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the development server:**
    A convenience script is provided to run the Flask development server on the correct port for preview.
    ```bash
    ./devserver.sh
    ```
    You can then view the application in your browser. The dashboard is available at `/api/access/dashboard`.

## Disclaimer and Limitation of Liability

This software is provided "AS IS" for educational and demonstration purposes only.

The creators and contributors of this project are not responsible for any misuse of this software. By using this application, you agree that you are solely responsible for your actions and for complying with all applicable local, state, and federal laws regarding data privacy, tracking, and surveillance.

Under no circumstances shall the authors or contributors be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software. It is your responsibility to ensure that your use of this software is ethical and legal.
