# Credit Underwriting Engine

A Python-powered automated risk assessment engine and Streamlit web application designed to evaluate loan applicants and streamline credit decision-making. The engine processes financial metrics to determine creditworthiness, assess risk levels, and output structured underwriting recommendations.

## 🚀 Live Demo
The application is hosted and available to test online at:
👉 **[credit-underwriting-engine Streamlit App](https://credit-underwriting-engine-8hehtpvzfg2cguvhqs3qpb.streamlit.app/)**

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
**SRINIVASTA / Credit Underwriting Engine**  
*Building the future of autonomous risk management.*
* **Lead Architect & Developer:** [Srinivasta](https://github.com/SRINIVASTA)

### Connect with Me
- [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/srinivas-t-a-557637119/)  
- [![Kaggle](https://img.shields.io/badge/Kaggle-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/srinivasta)  
- [![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:tasrinivass@gmail.com)  
- [![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/srinivasta)



---
---

## 📄 License
This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
