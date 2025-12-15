# Chergpt-Basic: Custom Chat Assistant  

Chergpt-Basic is a **simplified, login-free ChatGPT-like interface** designed for quick deployment and educational use.  

- ✅ Mobile-friendly  
- ✅ Easy to deploy on [Streamlit](https://streamlit.io/)  
- ✅ Beginner-friendly
- 🆕 RAG support (Retrieval-Augmented Generation via vector embeddings)
- 🔒 Optional password protection (global and admin)
- 📊 Built-in chat analytics and logging
- 📚 PDF document processing for context-aware responses

## Desktop Preview
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/73912243-d638-4b48-a2a8-2ed54d79ec80)  

## Mobile Preview
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/d77d5654-699a-405e-a65d-880f983b22b4)

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quickstart](#-quickstart-copypaste-setup)
- [Installation](#-installation)
  - [Local Development Setup](#local-development-setup)
  - [Deploy on Streamlit Cloud](#3-deploy-on-streamlit)
- [Configuration](#-configuration)
- [Use Cases](#-use-cases)
- [Live Examples](#-live-examples)
- [Troubleshooting](#-troubleshooting)
- [Documentation & Resources](#-documentation--resources)
- [Contributing](#-contributing)

---

## 🌟 Features  

### Core Capabilities
- **Custom Instructions**: Add tailored instructions to guide student or user interactions
- **Chat Logging**: Automatically store all conversations in a PostgreSQL database (NeonDB)
- **Analytics Dashboard**: Generate learning/teaching analytics from chatlogs
- **Download Chatlogs**: Export chat history as CSV for analysis
- **User Name Tracking**: Track conversations by user name

### Advanced Features
- **🧠 RAG Support (Retrieval-Augmented Generation)**: 
  - Upload PDF documents through the admin web interface
  - Automatic text extraction, chunking, and embedding generation
  - Context-aware responses using pgvector similarity search
  - Support for multiple PDF files with duplicate detection
  - Secure in-memory processing (files never stored on disk)
  - Smart query detection for context retrieval
  
- **🔒 Password Protection**: 
  - **Admin Password**: Protects admin panel for managing instructions, uploading PDFs, and viewing analytics
  - **Global Password**: Optional single password to restrict access to the entire application
  - See [Streamlit authentication guide](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso) for additional options

- **📱 Mobile Responsive**: Optimized interface for both desktop and mobile devices
- **☁️ Cloud Ready**: Easy deployment on Streamlit Cloud with simple configuration

---

## 📦 Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.8 or higher** installed on your system
2. **OpenAI API Key** - [Get one here](https://platform.openai.com/account/api-keys)
3. **NeonDB Account** (free tier available) - [Sign up here](https://console.neon.tech/)
4. **Git** (for cloning the repository)
5. **Streamlit Account** (for cloud deployment) - [Create account](https://streamlit.io/)

### System Requirements
- Operating System: Windows, macOS, or Linux
- RAM: Minimum 2GB (4GB recommended for PDF processing)
- Disk Space: At least 500MB free space
- Internet connection for API calls

---

## ⚡ Quickstart (copy–paste setup)  

**Want to deploy immediately?** You only need **4 configuration values** in your `secrets.toml`:  

```toml
OPENAI_API_KEY = "your_api_key_here"
DB_CONNECTION_STRING = "your_neondb_string_here"
ADMIN_PASSWORD = "set_this_to_what_you_want"
GLOBAL_PASSWORD = "optional_password_here"
```

### Quick Reference:
- **OPENAI_API_KEY**: Get from [OpenAI API Keys](https://platform.openai.com/account/api-keys)
- **DB_CONNECTION_STRING**: Get from [NeonDB Console](https://console.neon.tech/) after creating a project
- **ADMIN_PASSWORD**: **Required** - Create your own secure password for admin access
- **GLOBAL_PASSWORD**: **Optional** - Set this to require a password for all users to access the app

👉 Once these are configured, proceed to [Deploy on Streamlit](#3-deploy-on-streamlit) and you're live!

---

## 🛠️ Installation

### Local Development Setup

Follow these steps to run Chergpt-Basic on your local machine:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/String-sg/chergpt-basic.git
cd chergpt-basic
```

#### Step 2: Create a Virtual Environment (Recommended)

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

The required packages include:
- `streamlit` - Web application framework
- `openai` - OpenAI API client
- `psycopg2-binary` - PostgreSQL database adapter
- `PyPDF2` - PDF text extraction
- `tiktoken` - Token counting for embeddings
- `pgvector` - Vector similarity search support
- `pytest` - Testing framework
- `streamlit-feedback` - User feedback components

#### Step 4: Set Up Configuration

Create a `.streamlit/secrets.toml` file in your project directory:

```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

Add your configuration (see [Configuration section](#-configuration) below):

```toml
OPENAI_API_KEY = "sk-..."
DB_CONNECTION_STRING = "postgresql://user:password@host/database"
ADMIN_PASSWORD = "your_secure_admin_password"
GLOBAL_PASSWORD = "optional_global_password"  # Optional
```

#### Step 5: Run the Application

```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🔧 Configuration

### Database Setup (NeonDB)

1. **Create a NeonDB Account**: Go to [https://console.neon.tech/](https://console.neon.tech/)
2. **Create a New Project**: 
   - Click "Create Project"
   - Choose a project name
   - Select a region (choose Singapore or closest to your users)
3. **Get Connection String**:
   - Navigate to your project dashboard
   - Click on "Connection Details"
   - Copy the connection string (it looks like: `postgresql://user:password@host/database`)
   - Use this as your `DB_CONNECTION_STRING`

**Note**: The free tier of NeonDB provides:
- 3GB storage
- Always available (no hibernation)
- Perfect for small to medium deployments

### OpenAI API Setup

1. **Create an OpenAI Account**: Visit [https://platform.openai.com/](https://platform.openai.com/)
2. **Generate API Key**:
   - Go to [API Keys page](https://platform.openai.com/account/api-keys)
   - Click "Create new secret key"
   - **Important**: Copy and save the key immediately (you won't be able to see it again)
3. **Add Credits**: Ensure your OpenAI account has available credits for API usage

**Pricing Information**:
- The app uses `gpt-4o-mini` by default (cost-effective)
- Embeddings use `text-embedding-ada-002`
- Monitor usage in your [OpenAI dashboard](https://platform.openai.com/usage)

**💡 Beginner Tip**: Follow [this step-by-step guide](https://teachertech.beehiiv.com/p/api-openai) for detailed instructions on getting your OpenAI API key.

### Password Configuration

**Admin Password (Required)**:
- Set `ADMIN_PASSWORD` in your secrets.toml
- Grants access to:
  - Custom instruction editing
  - PDF upload and RAG management
  - Chat log analytics and downloads
  - App title and description customization

**Global Password (Optional)**:
- Set `GLOBAL_PASSWORD` if you want to restrict general access
- When configured, all users must enter this password to use the chat
- Leave empty or omit to allow unrestricted access to the chat interface

### RAG (PDF Upload) Configuration

No additional configuration needed! Once your database is set up:
1. Log in as admin (using `ADMIN_PASSWORD`)
2. Navigate to "📤 Upload New Materials" in the sidebar
3. Upload PDF files (up to 50MB, max 1000 pages)
4. Files are processed automatically and made searchable

**Security Features**:
- Files are processed entirely in memory
- Original PDFs are never stored on disk
- Only text chunks and embeddings are stored in the database
- Automatic duplicate detection prevents re-processing

---

## 🚀 Getting Started with Deployment

There are **3 simple steps** to deploy your own Chergpt-Basic app:  

1. **Set up your database** (for storing chatlogs).  
2. **Get your OpenAI API key**.  
3. **Deploy to Streamlit**.  

---

### 1. Set up your backend (Database)  

We recommend [**NeonDB**](https://console.neon.tech/) (free tier works well).  

1. Create an account at [Neon](https://console.neon.tech/).  
2. Start a free project (choose **Singapore** region if relevant).  
3. Copy your **DB connection string** — you'll need this later.  

📌 This string is what allows Chergpt-Basic to save chat data. Keep it safe.  

---

### 2. Get your OpenAI API key  

1. Go to [OpenAI API keys](https://platform.openai.com/account/api-keys).  
2. Click **Create new secret key**.  
3. Copy it somewhere safe — you'll need it for deployment.  

💡 Not sure how? Follow [this beginner-friendly guide](https://teachertech.beehiiv.com/p/api-openai).  

---

### 3. Deploy on Streamlit  

Click below to auto-deploy:  
👉 [**Deploy Chergpt-Basic**](https://share.streamlit.io/deploy)  

Then:  

1. Create a **Streamlit account** (free).  
2. Connect your **GitHub account**.
3. Fork the repo → `String-sg/Chergpt-basic`.  
4. In **Advanced Settings → Secrets.toml**, paste:  

   ```toml
   OPENAI_API_KEY = "your_api_key_here"
   DB_CONNECTION_STRING = "your_neondb_string_here"
   ADMIN_PASSWORD = "set this to what you want"
   GLOBAL_PASSWORD = "optional_password_here"
   ```

#### Alternative: Deploy without GitHub Account

Don't have a GitHub account and just want to deploy without cloning? Sure, you can!

1. Go to [streamlit.io](https://streamlit.io/) and create an account, then login
2. In the top right corner, click **Create app**

   <img width="754" height="87" alt="image" src="https://github.com/user-attachments/assets/80b95beb-9c77-4e1f-a90a-8d75a7a34a79" />

3. Select **Deploy a public app from Github**

   <img width="1087" height="393" alt="image" src="https://github.com/user-attachments/assets/85611478-6ea1-4aa2-8229-725cab9f5744" />

4. Setup your app with the following fields:
   - Repository = `https://github.com/String-sg/chergpt-basic/` (You can click "Paste Github URL" and enter this)
   - Branch = `main`
   - Main file path = `main.py`
   - APP URL = choose your own or use the default

   <img width="821" height="643" alt="image" src="https://github.com/user-attachments/assets/d55f4c30-9cff-4282-88aa-2f2c3c34f8da" />

5. Click on **Advanced settings**, paste in the configuration details you previously obtained

   <img width="859" height="620" alt="image" src="https://github.com/user-attachments/assets/0d5506bc-c5c7-4b6b-8c86-96fb2211560d" />

---

## 🎯 Use Cases  

Chergpt-Basic is ideal for educational and interactive scenarios:

### 1. **Educational Role-Play & Personas**
Create immersive learning experiences by configuring the chatbot to assume different roles:
- **Historical Figures**: Students can interview historical personalities (e.g., Albert Einstein, Marie Curie)
- **Medical Scenarios**: Practice patient interactions for healthcare training
- **Character Role-Play**: Language learning through conversational practice with fictional characters

**Example Setup**:
```
Custom Instructions: "You are Isaac Newton. Respond to students' questions about 
physics and mathematics from the perspective of a 17th-century scientist. Use 
historical context but explain concepts clearly."
```

### 2. **Guided Language Learning**
Build interactive "escape rooms" or challenge-based learning:
- **Chinese Language Tasks**: Students complete tasks like ordering food, asking for directions
- **Spanish Conversation Practice**: Progressive difficulty levels with checkpoint validation
- **Vocabulary Building**: Contextual word usage in realistic scenarios

**Example Setup**:
```
Custom Instructions: "You are a shopkeeper in Shanghai. Only respond in Mandarin Chinese. 
Help students practice ordering items. After they successfully order 3 items, 
congratulate them and move to the next checkpoint."
```

### 3. **Interactive Lessons with Analytics**
Run structured lessons and monitor student progress:
- Track student questions and responses
- Identify common misconceptions through chat log analysis
- Generate summaries of learning patterns
- Download data for further analysis

**Example Use**:
- Physics problem-solving sessions
- Economics concept explanations with RAG-powered textbook references
- Step-by-step programming tutorials

### 4. **Subject-Specific Tutoring with RAG**
Upload course materials (PDFs) to create a subject-specific tutor:
- **Economics Tutor**: Upload textbooks, lecture notes, and the bot answers from course materials
- **Science Lab Assistant**: Upload lab manuals for procedure guidance
- **Legal Studies**: Upload case law documents for reference-based learning

**How it Works**:
1. Admin uploads relevant PDF documents
2. System automatically processes and creates searchable embeddings
3. Student asks a question
4. Bot searches uploaded materials for relevant context
5. Responds with context-aware answers based on course materials

### 5. **Assessment & Quiz Modes**
Configure the bot to conduct assessments:
- Multiple-choice quizzes with instant feedback
- Open-ended questions with guided responses
- Practice exams with performance tracking

---

## 🚀 Live Examples  

See Chergpt-Basic in action:

- [Physics (Lookang fork)](https://chergpt-physics-lookang.streamlit.app/) - Interactive physics tutoring
- [Physics (CPDD deployment)](https://chergpt-physics-cpdd.streamlit.app/) - Physics education platform

These examples showcase different configurations and use cases for educational purposes.

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Errors

**Issue**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- Verify your `DB_CONNECTION_STRING` is correct in `secrets.toml`
- Check that your NeonDB project is active (not suspended)
- Ensure you're using the correct connection string format: `postgresql://user:password@host/database`
- Test the connection string using a PostgreSQL client or command line:
  ```bash
  psql "your_connection_string_here"
  ```

**Tip**: The connection string should look like: `postgresql://username:password@ep-xxxxx.region.aws.neon.tech/neondb`

---

#### 2. OpenAI API Errors

**Issue**: `openai.error.AuthenticationError: Incorrect API key provided`

**Solutions**:
- Verify your API key in `secrets.toml` starts with `sk-`
- Ensure there are no extra spaces or quotes in the key
- Check that your OpenAI account has available credits
- Generate a new API key from [OpenAI dashboard](https://platform.openai.com/account/api-keys)

**Issue**: `Rate limit exceeded`

**Solutions**:
- Wait a few minutes before retrying
- Upgrade your OpenAI plan for higher rate limits
- Reduce the frequency of requests in your application

---

#### 3. PDF Upload Issues

**Issue**: `File too large` or `Processing failed`

**Solutions**:
- Ensure PDF is under 50MB
- Check PDF page count is under 1,000 pages
- Verify PDF is not encrypted or password-protected
- Try converting the PDF to a simpler format (remove images if possible)

**Issue**: `No text extracted from PDF`

**Solutions**:
- PDF might be image-based (scanned) - use OCR tools first
- Try opening the PDF and copying text manually to verify it contains extractable text
- Use a different PDF or re-save the document

---

#### 4. Streamlit Deployment Issues

**Issue**: `ModuleNotFoundError: No module named 'xyz'`

**Solutions**:
- Verify `requirements.txt` contains all dependencies
- Check that Streamlit Cloud is using the correct Python version (3.8+)
- Rebuild the app from Streamlit Cloud dashboard

**Issue**: `Secrets not found`

**Solutions**:
- Go to Streamlit Cloud dashboard → Your App → Settings → Secrets
- Ensure all required secrets are defined:
  ```toml
  OPENAI_API_KEY = "sk-..."
  DB_CONNECTION_STRING = "postgresql://..."
  ADMIN_PASSWORD = "your_password"
  ```
- Click "Save" after adding secrets
- Reboot the app

---

#### 5. Admin Login Not Working

**Issue**: "Incorrect password" even with correct password

**Solutions**:
- Check for extra spaces in `ADMIN_PASSWORD` in `secrets.toml`
- Ensure you're entering the password exactly as defined
- Clear browser cache and cookies
- Try in an incognito/private browser window

---

#### 6. RAG Not Retrieving Context

**Issue**: Uploaded PDFs but no context is retrieved

**Solutions**:
- Verify PDFs were successfully processed (check admin panel → RAG Management)
- Ensure RAG is enabled in admin settings (toggle should be ON)
- Check that your query is related to the uploaded content
- Review the similarity threshold - lower it if needed in the code

**Issue**: `pgvector extension not found`

**Solutions**:
- Ensure NeonDB has pgvector extension enabled (should be automatic)
- Try running the initialization manually from admin panel
- Contact NeonDB support if the extension is not available

---

#### 7. Local Development Issues

**Issue**: `streamlit: command not found`

**Solutions**:
- Ensure virtual environment is activated
- Reinstall streamlit: `pip install streamlit`
- Check Python PATH: `which python` or `where python`

**Issue**: Port 8501 already in use

**Solutions**:
- Kill existing Streamlit process: 
  - Windows: `taskkill /F /IM streamlit.exe`
  - Mac/Linux: `pkill -f streamlit`
- Run on different port: `streamlit run main.py --server.port 8502`

---

#### 8. Performance Issues

**Issue**: Slow response times

**Solutions**:
- Check OpenAI API status: [status.openai.com](https://status.openai.com)
- Verify database performance (NeonDB free tier may have limits)
- Reduce RAG chunk retrieval count (modify `top_k` parameter)
- Consider upgrading to a paid plan for better performance

---

### Getting Additional Help

If you encounter issues not covered here:

1. **Check existing GitHub issues**: [GitHub Issues](https://github.com/String-sg/chergpt-basic/issues)
2. **Create a new issue**: Include:
   - Error messages (sanitize sensitive information)
   - Steps to reproduce
   - Your environment (Python version, OS)
   - Deployment method (local vs Streamlit Cloud)
3. **Streamlit Community Forum**: [discuss.streamlit.io](https://discuss.streamlit.io/)
4. **Review logs**: Check Streamlit Cloud logs or terminal output for detailed error messages

---

## 📚 Documentation & Resources

### Official Documentation

- **Streamlit Documentation**: [https://docs.streamlit.io/](https://docs.streamlit.io/)
  - [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
  - [Authentication Options](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso)
  - [Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)

- **OpenAI API Documentation**: [https://platform.openai.com/docs](https://platform.openai.com/docs)
  - [Chat Completions API](https://platform.openai.com/docs/guides/chat)
  - [Embeddings API](https://platform.openai.com/docs/guides/embeddings)
  - [Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)

- **NeonDB Documentation**: [https://neon.tech/docs](https://neon.tech/docs)
  - [Connection Strings](https://neon.tech/docs/connect/connect-from-any-app)
  - [pgvector Extension](https://neon.tech/docs/extensions/pgvector)

### Related Technologies

- **pgvector**: Vector similarity search for PostgreSQL
  - [GitHub Repository](https://github.com/pgvector/pgvector)
  - [Usage Guide](https://github.com/pgvector/pgvector#getting-started)

- **PyPDF2**: PDF text extraction
  - [Documentation](https://pypdf2.readthedocs.io/)

- **Tiktoken**: Token counting library
  - [GitHub Repository](https://github.com/openai/tiktoken)

### Tutorials & Guides

- **Getting OpenAI API Key**: [Teacher Tech Guide](https://teachertech.beehiiv.com/p/api-openai) - Beginner-friendly walkthrough
- **RAG (Retrieval-Augmented Generation)**: Understanding how context-aware AI works
- **Prompt Engineering**: [OpenAI Guide](https://platform.openai.com/docs/guides/prompt-engineering) - Writing effective custom instructions

### Community & Support

- **GitHub Repository**: [String-sg/chergpt-basic](https://github.com/String-sg/chergpt-basic)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/String-sg/chergpt-basic/issues)
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io/)

### Example Projects & Inspiration

- **Streamlit Gallery**: [https://streamlit.io/gallery](https://streamlit.io/gallery)
- **OpenAI Cookbook**: [https://github.com/openai/openai-cookbook](https://github.com/openai/openai-cookbook)

---

## 🤝 Contributing

We welcome contributions to Chergpt-Basic! Here's how you can help:

### Ways to Contribute

1. **Report Bugs**: Open an issue on GitHub with details about the bug
2. **Suggest Features**: Share your ideas for new features or improvements
3. **Submit Pull Requests**: Fix bugs or add features
4. **Improve Documentation**: Help make the README and docs better
5. **Share Use Cases**: Tell us how you're using Chergpt-Basic

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/chergpt-basic.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes and test thoroughly
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Open a Pull Request

### Testing

Run the test suite before submitting PRs:

```bash
pytest
```

Run specific tests:
```bash
pytest test_rag.py
pytest test_user_storage.py
pytest app_test.py
```

### Code Style

This project uses Pylint for code quality. Run it locally:

```bash
pylint $(git ls-files '*.py')
```

---

## 📄 License

This project is open source. Please check the repository for license details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/)
- Database by [NeonDB](https://neon.tech/)
- Vector search using [pgvector](https://github.com/pgvector/pgvector)

---

## 📧 Contact

For questions, issues, or collaboration opportunities:
- Open an issue on [GitHub](https://github.com/String-sg/chergpt-basic/issues)
- Check existing documentation and troubleshooting guide above

---

**Made with ❤️ for educators and learners**
