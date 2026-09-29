# TailMemory

> A maintenance assistant that remembers what every previous shift already tried on this airframe.

TailMemory is an advisory prototype for aircraft maintenance teams. A user selects a synthetic aircraft tail number, describes a current fault, recalls relevant history from Hindsight Cloud, and receives a structured Groq advisory grounded in that aircraft-specific evidence.

## Why persistent memory matters

Without memory, an assistant can recommend a generic intervention that the aircraft has already tried. TailMemory makes the remembered history visible and marks previously failed actions so a qualified engineer can review a different verification path.
# TailMemory

## AI-Powered Aircraft Maintenance Memory Assistant

TailMemory is an AI-powered aircraft maintenance assistant built with Streamlit. It helps retrieve relevant historical maintenance memories for a selected aircraft and uses those memories to provide an AI-generated maintenance advisory.

The project uses **Hindsight Cloud** for aircraft-specific memory and **Groq** for generating the maintenance response.

> **Note:** TailMemory is an advisory prototype. Maintenance decisions remain with appropriately qualified personnel. All aircraft records used in the project are synthetic.

## Project Purpose

TailMemory demonstrates how aircraft-specific maintenance history can be combined with AI to help users recall previous maintenance events and obtain context-aware maintenance insights from historical information.

---

## Features

* Select an aircraft tail number.
* Select an ATA chapter.
* Enter the current aircraft fault.
* Retrieve relevant historical maintenance memories.
* Generate an AI-based maintenance advisory.
* Display supporting maintenance evidence.
* Show previous actions and their outcomes.
* Record feedback about recommended actions.
* View the maintenance timeline.
* Compare maintenance history between aircraft.
* View evaluation results.

---

## How It Works

```text
User enters current fault
          |
          v
   Aircraft / ATA Selection
          |
          v
    Hindsight Cloud
          |
          v
Relevant Maintenance Memories
          |
          v
       Groq LLM
          |
          v
 Maintenance Advisory
          |
          v
     User Feedback
          |
          v
   Updated Memory
```

The system uses the selected aircraft tail number when retrieving maintenance memories so that the retrieved history remains specific to that aircraft.

---

## Technology Stack

| Technology      | Purpose                         |
| --------------- | ------------------------------- |
| Python          | Application development         |
| Streamlit       | Web application interface       |
| Hindsight Cloud | Aircraft maintenance memory     |
| Groq            | AI response generation          |
| Pandas          | Data processing                 |
| Pydantic        | Data validation                 |
| Matplotlib      | Evaluation and visualization    |
| Requests        | API communication               |
| python-dotenv   | Environment variable management |
| Pytest          | Testing                         |

---

## Project Structure

```text
tailmemory/
│
├── app/
│   ├── main.py
│   └── config.py
│
├── backend/
│   ├── agent/
│   │   └── llm.py
│   │
│   └── memory/
│       └── hindsight_client.py
│
├── data/
│   └── synthetic/
│
├── evaluation/
│
├── tests/
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requirements

* Python 3.11
* Hindsight Cloud account and API credentials
* Groq API key
* Internet connection for external API access

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Asfiashub/Aircraft-Maintenance-Memory.git
```

Go into the project directory:

```bash
cd Aircraft-Maintenance-Memory/tailmemory
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the `tailmemory` directory.

Add the required credentials:

```env
GROQ_API_KEY=your_groq_api_key
HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BASE_URL=your_hindsight_base_url
HINDSIGHT_BANK_ID=your_hindsight_bank_id
```

Do not upload your `.env` file or API keys to GitHub.

---

## Running the Application

From the `tailmemory` directory, run:

```bash
streamlit run app/main.py
```

Streamlit will start the application and provide a local URL in the terminal.

---

## Application Workflow

### 1. Select Aircraft

The user selects the aircraft tail number from the sidebar.

### 2. Select ATA Chapter

An ATA chapter can be selected to focus the maintenance context.

### 3. Enter Current Fault

The user describes the current aircraft fault.

Example:

```text
Hydraulic pressure warning after takeoff.
```

### 4. Retrieve Maintenance Memory

TailMemory uses Hindsight Cloud to retrieve relevant historical maintenance events associated with the selected aircraft.

### 5. Generate Advisory

The retrieved memories and current fault are used to generate an AI maintenance advisory through Groq.

The response can include:

* Likely fault category
* Relevant previous events
* Previous actions
* Previous outcomes
* Suggested verification steps

### 6. Review Evidence

The application displays the maintenance memories used as evidence for the response.

### 7. Record Feedback

The user can record the outcome of a recommended action. This feedback can be stored as additional maintenance memory.

---

## Maintenance Timeline

TailMemory provides a maintenance timeline for the selected aircraft.

The timeline allows users to review previous maintenance events and filter the information based on the available maintenance context.

---

## Cross-Tail Comparison

The application provides a comparison between aircraft maintenance histories.

This helps demonstrate the importance of maintaining aircraft-specific memory instead of treating maintenance events from different aircraft as the same history.

---

## Evaluation

The project includes an evaluation section for reviewing the system's results.

Evaluation functionality can be run using:

```bash
python -m evaluation.evaluate
```

The project also contains synthetic maintenance records and evaluation data used to test the application.

---

## Data

The project uses **synthetic aircraft maintenance records**.

The data is intended for:

* Demonstrating aircraft-specific memory
* Testing maintenance retrieval
* Demonstrating AI-assisted diagnosis
* Evaluating the application

The data should not be treated as actual aircraft maintenance records.

---

## Safety and Scope

TailMemory is an **AI-assisted maintenance memory and advisory prototype**.

It is not intended to replace:

* Qualified maintenance personnel
* Aircraft maintenance manuals
* Approved maintenance procedures
* Official aircraft records
* Regulatory requirements

Maintenance decisions remain with appropriately qualified personnel.

---

## Deployment

The application can be deployed using a Streamlit-compatible hosting service.

For deployment, make sure:

1. `requirements.txt` is present.
2. Required environment variables are configured.
3. API keys are stored as secrets rather than committed to GitHub.
4. The application entry point is:

```text
tailmemory/app/main.py
```

The Python version used for deployment should be **Python 3.11**.

---

## Dependencies

The project uses the following main dependencies:

```text
pandas>=2.2
pydantic>=2.7
python-dotenv>=1.0
pytest>=8.0
requests>=2.32
streamlit>=1.40
```

---

## Repository

GitHub:

```text
https://github.com/Asfiashub/Aircraft-Maintenance-Memory
```

---

