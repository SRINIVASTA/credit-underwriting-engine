# Credit Underwriting Engine

A Python-powered automated risk assessment engine and Streamlit web application designed to evaluate loan applicants and streamline credit decision-making. The engine processes financial metrics to determine creditworthiness, assess risk levels, and output structured underwriting recommendations.

## 🚀 Live Demo
The application is hosted and available to test online at:
👉 **[credit-underwriting-engine Streamlit App](https://streamlit.app)**

---

## 🛠️ Project Structure
The repository contains the following core files:
*   `underwriting_core.py`: The underlying rule engine and logic that evaluates applicant creditworthiness.
*   `app.py`: The frontend UI wrapper built using Streamlit.
*   `test_underwriting.py`: Unit tests to validate scoring logic and financial math boundaries.
*   `requirements.txt`: Python package dependencies required to run the engine.

---

## 💻 Installation & Local Setup

Follow these steps to clone, configure, and execute the credit underwriting engine on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com
cd credit-underwriting-engine
```

### 2. Configure Your Virtual Environment
It is highly recommended to isolate dependencies using a virtual environment:
```bash
# Create the environment
python -m venv venv

# Activate the environment (Mac/Linux)
source venv/bin/activate

# Activate the environment (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies
Install all required packages listed in the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
Launch the frontend dashboard interface locally:
```bash
streamlit run app.py
```
*Once running, navigate to `http://localhost:8501` in your browser.*

---

## 🧪 Running Unit Tests
To verify the math, rule thresholds, and edge cases inside `underwriting_core.py`, execute the test suite using `pytest`:
```bash
# Install pytest if not already in requirements
pip install pytest

# Run the test file
pytest test_underwriting.py -v
```

---

## 📄 License
This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
