

# 🔍 VBOT – RAG-Based Chat Application Using LLMs


## 📌 Project Overview

**Goal**: Enable natural language querying over institutional data using a RAG-based AI chatbot.

**Models Used**: Meta LLaMA 3 (8B & 13B), FAISS for vector retrieval, BERT for embeddings, T5 for summarization.

**Interface**: Chat-based UI built with Chainlit for interactive document and query handling.

**Input**: Natural language queries + uploaded documents (e.g., academic PDFs, SQL data).

**Output**: Context-aware, factually grounded answers derived from structured and unstructured sources.

---

## 🧪 Sample Input/Output

**Input**:  
Query – *"Show all students who scored above 90 in Data Structures"*  
Platform – VBOT Chat Interface  
AI Model – Meta LLaMA 3 + FAISS  

**Output**:
```
[
  {"Name": "Ananya Sharma", "Roll No": "20CSE045", "Score": 94},
  {"Name": "Rajeev Nair", "Roll No": "20CSE078", "Score": 91},
  ...
]
Query Source: student_results.pdf
Retrieval Confidence: High
```

---

## 🤖 Models Used

- **Meta LLaMA 3 (8B/13B)** – For natural language response generation  
- **FAISS** – For fast similarity search over vector embeddings  
- **BERT** – Used for semantic embedding and document ranking  
- **T5** – For summarization of long document responses  
- **DistilBERT** – (Optional) lightweight transformer for quick inference  
- **Cross-Encoders / Re-rankers** – For refining top-k retrieval accuracy

---

## 📁 Dataset

**Documents & Sources**:
- Uploaded PDFs (student data, course files, transcripts)
- SQL Databases (structured institutional records)
- Sample Dataset File: `institutional_data.xlsx` *(not public)*

**Columns in Structured Data**:
- Student Name, Roll Number, Course Code, Faculty, Marks, Attendance, GPA, etc.

---

## 🚀 Features

- Natural language Q&A over your own documents and databases  
- Multi-turn chat with context retention  
- Document upload + SQL DB querying  
- PDF parsing, vectorization, semantic search  
- Role-based access control (RBAC)  
- Flexible prompt customization: Summarize / Explain / Opinion  

---

## 🛠 Installation

```bash
git clone https://github.com/Dherandar08102003/VBOT.git
cd VBOT
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate for Windows
pip install -r requirements.txt
```

---

## ⚙️ Configuration

- `params.yaml`: Set vector dimensions, DB connection, model paths, etc.  
- `schema.yaml`: Define table structures and metadata formats  

---

## 💡 How to Use

```bash
python app.py
```

1. Upload your document (PDF or CSV)
2. Type your query in natural language
3. View precise, explainable AI responses  
4. Follow up with multi-turn queries

---

## 📂 Project Structure

```
VBOT/
├── app.py                 # Entry point
├── requirements.txt       # Dependencies
├── params.yaml            # Configs
├── schema.yaml            # Database schema
├── src/
│   ├── data_ingestion/    # Data ingestion logic
│   ├── preprocessing/     # Clean, chunk, embed text
│   ├── models/            # Retrieval + generation modules
│   └── utils/             # Common functions
├── artifacts/             # Vector DBs, Logs, Saved Models
├── public/                # UI static assets
└── test.ipynb             # Sample test notebook
```

---

## 🧠 Key Technologies

- **Hugging Face Transformers**
- **LangChain**
- **FAISS**
- **Chainlit UI**
- **PyMuPDF**
- **GraphDB / Neo4j**
- **SQLAlchemy** for database integration

---

## 🤝 Contributing

1. Fork this repository  
2. Create a new branch: `git checkout -b your-feature-name`  
3. Commit your changes  
4. Push to your fork  
5. Open a pull request 🚀



## 📬 Contact

For feedback, bugs, or feature requests, please open an issue in the [GitHub Issues](https://github.com/Dherandar08102003/VBOT/issues) section.

---

Let me know if you'd like this exported as a downloadable `README.md` file or further tailored to match GitHub README aesthetics!
