# Chergpt-Basic: Custom Chat Assistant

Chergpt-Basic is a simplified, login-free ChatGPT-like interface designed for quick deployment. It allows users to interact with a chat assistant based on OpenAI's GPT-3.5 model. The README provides clear instructions on setting up the backend, customization, and potential use cases.

## Deployment 
-  https://chergpt-physics-lookang.streamlit.app/ from my own forked GitHub 
-  https://chergpt-physics-cpdd.streamlit.app/  from Kah How's deployment

## Features
- [x] Set custom instructions to guide student interactions.
- [WIP] Trigger immediate summaries of learning insights at the end of the session.

Need to secure access with a simple global password? Check the [authentication guide](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso).

## Use Cases
Chergpt-Basic enables a variety of use cases, with the primary one being the creation of user personas for students to interact with. Examples include historical figures or patients with specific medical conditions.

## How to setup backend 
We recommend using **NeonDB** 
You can follow instructions on NeonDB [here](https://start.open.gov.sg/docs/getting-started/prerequisites) <br>


## Secrets.toml File Structure
In the `secrets.toml` file, specify three items: you have to change it to your own

```
OPENAI_API_KEY = "sk-Co6R5h4RcT....................................." 
ADMIN_PASSWORD= "passwordyourchoice" 
DB_CONNECTION = "postgresql://chergpt:PGPASSWORD@some-details-based-on-connection-string.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" 
```
- See [here](https://teachertech.beehiiv.com/p/api-openai) if you're unsure how to create it.
- Used to gate access for updating custom instructions.
- Refer to instructions above on **How to Set Up Backend** if unsure.

Feel free to explore and enhance the functionality of Chergpt-Basic according to your specific needs!
