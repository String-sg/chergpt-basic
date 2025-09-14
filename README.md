# Chergpt-Basic: Custom Chat Assistant  

Chergpt-Basic is a **simplified, login-free ChatGPT-like interface** designed for quick deployment.  

- ✅ Mobile-friendly  
- ✅ Easy to deploy on [Streamlit](https://streamlit.io/)  
- ✅ Beginner-friendly
- 🆕 Now with RAG support (via vector embeddings via the admin web-interface)

## Desktop Preview
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/73912243-d638-4b48-a2a8-2ed54d79ec80)  

## Mobile Preview
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/d77d5654-699a-405e-a65d-880f983b22b4)  

---

## ⚡ Quickstart (copy–paste setup)  


Before deploying, you only need **3 things** in your `Secrets.toml`:  

```toml
OPENAI_API_KEY = "your_api_key_here"
DB_CONNECTION_STRING = "your_neondb_string_here"
ADMIN_PASSWORD = "set this to what you want"
GLOBAL_PASSWORD = "optional_password_here"
```

**Don't have the values? Detailed instructions in the section below**
OPENAI_API_KEY = from OpenAI
DB_CONNECTION_STRING: from NeonDB
ADMIN_PASSWORD: compulsory, you need this to setup and customize your bot 
GLOBAL_PASSWORD: optional, lets you restrict access with a single password

👉 Once these are set, head to Deploy on Streamlit
 and you’re live!
## 🌟 Features  

- Add **custom instructions** to guide student interactions.  
- **Download chatlogs** for later analysis.  
- Generate **learning/teaching analytics** from chatlogs.  
- Optional **password protection** (see [authentication guide](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso)).  

---

## 🎯 Use Cases  

Chergpt-Basic can be used for:  

- Creating **student personas** (e.g. historical figures, patients, role-play scenarios).  
- Building **guided escape rooms** for language learning (e.g. Chinese with tasks as checkpoints).  
- Running **interactive lessons** with analytics feedback.  

---

## 🚀 Live Examples  

- [Physics (Lookang fork)](https://chergpt-physics-lookang.streamlit.app/)  
- [Physics (CPDD deployment)](https://chergpt-physics-cpdd.streamlit.app/)  

---

## 🛠️ Getting Started  

There are **3 simple steps** to deploy your own Chergpt-Basic app:  

1. **Set up your database** (for storing chatlogs).  
2. **Get your OpenAI API key**.  
3. **Deploy to Streamlit**.  

---

### 1. Set up your backend (Database)  

We recommend [**NeonDB**](https://console.neon.tech/) (free tier works well).  

1. Create an account at [Neon](https://console.neon.tech/).  
2. Start a free project (choose **Singapore** region if relevant).  
3. Copy your **DB connection string** — you’ll need this later.  

📌 This string is what allows Chergpt-Basic to save chat data. Keep it safe.  

---

### 2. Get your OpenAI API key  

1. Go to [OpenAI API keys](https://platform.openai.com/account/api-keys).  
2. Click **Create new secret key**.  
3. Copy it somewhere safe — you’ll need it for deployment.  

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

# Don't have a Github account and just want to deploy without cloning?
Sure, you can!<br>
Go to streamlit.io + create an account, login

In the top right corner, click create app
<img width="754" height="87" alt="image" src="https://github.com/user-attachments/assets/80b95beb-9c77-4e1f-a90a-8d75a7a34a79" />

Select **Deploy a public app from Github**
<img width="1087" height="393" alt="image" src="https://github.com/user-attachments/assets/85611478-6ea1-4aa2-8229-725cab9f5744" />

Setup your app with the following fields
- Repository = https://github.com/String-sg/chergpt-basic/ (You can click "Paste Github URL" and enter this)
- Branch = main
- Main file path = main.py
- APP URL = choose your own or use the default
<img width="821" height="643" alt="image" src="https://github.com/user-attachments/assets/d55f4c30-9cff-4282-88aa-2f2c3c34f8da" />

Click on advanced settings, paste in the details you previously obtained
<img width="859" height="620" alt="image" src="https://github.com/user-attachments/assets/0d5506bc-c5c7-4b6b-8c86-96fb2211560d" />
