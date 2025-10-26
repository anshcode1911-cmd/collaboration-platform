```markdown
# **Distributed Collaboration Platform - Milestone 1 Submission**

**Final Project (Milestone 1) for CS G623 Advanced Operating Systems, Semester I**  
*By Ansh, Praptipriya Phukon, Tathya Sethi*

This project is a distributed, multi-component platform that enables users to collaborate on documents in real-time. It features a robust **gRPC client-server architecture**, **user authentication**, **document management**, and a **mock LLM integration** for text assistance.

## Features Implemented 
- **gRPC Service Architecture**: Efficient communication between all components using gRPC.  
- **Authentication & Session Management**: Secure session tokens for user login and validation.  
- **Document Management**: Create, update, and view all documents on the platform (in-memory).  
- **Presence Awareness**: Users can see who else is online and active.  
- **LLM Integration (Mock)**: AI service for simulated text tasks (grammar check, summarize, etc.).  
- **Interactive Client**: A user-friendly command-line interface (CLI) for user interaction.

## Architecture
- **LLM Server** (Port 50052): Handles AI queries (grammar, summarization, suggestions)
- **Application Server** (Port 50051): Core business logic, authentication, document management
- **Client**: Interactive CLI for users

## Quick Start

### 1. **Installation**

Install dependencies from `requirements.txt`:

```bash
# It's recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt


### 2. Generate gRPC Code
```bash
python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/service.proto

### 3. Run the Services (in Order)
```bash
python run_llm_server.py
python run_app_server.py
python run_client.py

### Test Credentials

Use any of the predefined test users:
Username	Password
admin	admin123
user1	password1
user2	password2


```
