# Securing AI-Integrated APIs: A Content Moderation Case Study
This repository presents a security-focused case study that investigates vulnerabilities in AI-integrated APIs, using a content moderation system as the target domain. The project simulates real-world attack scenarios against a machine learning model and a Large Language Model (LLM) exposed exclusively through API endpoints, and evaluates mitigation strategies based on OWASP API Security Top 10 (2023) and OWASP LLM Top 10 (2025).

##  Case Study Overview

Modern AI systems are increasingly deployed behind APIs, enabling scalable access to machine learning classifiers and LLM-based services. While this architecture offers flexibility and usability, it also introduces security risks that span both **traditional API vulnerabilities** and **emerging AI-specific threats**, such as prompt injection.

This case study implements and compares **two versions of the same content moderation API**:

-   **Version 1 (Vulnerable)**  
    Designed with intentional security flaws to simulate a realistic but insecure deployment.
    
-   **Version 2 (Secured)**  
    Incorporates industry-recommended defenses to mitigate identified vulnerabilities.
    

By executing identical request patterns and simulated attacks against both versions, the project empirically demonstrates how security controls affect system behavior, resilience, and data exposure.

##  System Architecture

The system integrates:

-   **Machine Learning Model**
    
    -   Linear Support Vector Classifier (Linear SVC)
        
    -   Trained on a preprocessed content moderation dataset
        
    -   Achieves ~75% accuracy and serves as the primary classification engine
        
-   **Large Language Model (LLM)**
    
    -   TinyLlama
        
    -   Used as an explainability module to justify moderation decisions
        
-   **API Layer**
    
    -   Built with **FastAPI**
        
    -   Acts as the sole interaction point for users and attackers
        
    -   Orchestrates authentication, authorization, inference, and data access
        
-   **Database**
    
    -   SQLite for user data.
##  Security Focus

The project evaluates vulnerabilities aligned with:

### OWASP API Security Top 10 (2023)

-   Broken Object Level Authorization (API1)
    
-   Broken Authentication (API2)
    
-   Broken Object Property Level Authorization (API3)
    
-   Unrestricted Resource Consumption (API4)
    
-   Broken Function Level Authorization (API5)
    
-   Server-Side Request Forgery (API7)
    

### OWASP LLM Top 10 (2025)

-   Prompt Injection (LLM01)
    

----------

## Simulation Methodology

-   All attacks are **simulated in a controlled environment**
    
-   Experiments are executed via **Jupyter notebooks**
    
-   No destructive or large-scale denial-of-service attacks are performed
    
-   Resource-intensive vulnerabilities are analyzed through **architectural inspection**
    
-   Results are compared side-by-side between vulnerable and secured APIs
    

This approach prioritizes **reproducibility, safety, and empirical validation**.

----------

## Project Structure
```graphql
cm_model/
├── api/ # API routes and request handling
├── data/ # Datasets and sample inputs
├── modelling/ # ML model training and evaluation
├── notebook/ # Security simulations and experiments
├── templates/ # Prompt and request templates
├── app.py # FastAPI application entry point
├── inference.py # Request and attack orchestration
├── pipeline.py # Model inference logic
├── database.py # SQLite database helpers
├── config.py # Application and security configuration
├── requirements.txt # Python dependencies
└── v1_router.env # Environment variables for routing version 1
```

----------

## Installation

```
git clone https://github.com/Adexandria/cm_model.git cd cm_model

python -m venv .venv source .venv/bin/activate

pip install -r requirements.txt
``` 

----------

## Running the API

```
python app.py
```

The API will start locally and expose endpoints for:

-   Authentication & authorization
    
-   Content moderation inference
    
-   Model training (admin only)
    
-   LLM-based explainability
    

----------

## Experiments & Results

Security simulations include:

-   Authorization bypass (BOLA, BFLA)
    
-   Authentication flaws (brute force, weak credentials)
    
-   Data overexposure
    
-   Prompt injection attacks against the LLM
    

Each scenario is evaluated on:

-   **Version 1 (Vulnerable)** — exploit succeeds
    
-   **Version 2 (Secured)** — exploit mitigated or blocked
    

Results highlight how **simple architectural changes** (RBAC, rate limiting, input validation, prompt separation) dramatically improve system security.

----------

##  Key Mitigations Implemented (Version 2)

-   Role-Based Access Control (RBAC)
    
-   Strong password policies and account lockouts
    
-   JWT expiration and secure refresh token handling
    
-   Rate limiting and request quotas
    
-   Response filtering to prevent data leakage
    
-   Strict input validation (CSV schema enforcement)
    
-   XML-based prompt separation to mitigate LLM prompt injection

