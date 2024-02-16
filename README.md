# Chergpt-Basic: Custom Chat Assistant

Chergpt-Basic is a simplified, login-free ChatGPT-like interface designed for quick deployment. It allows users to interact with a chat assistant based on OpenAI's GPT-3.5/ GPT-4 model. 

## Deployment - examples
-  https://chergpt-physics-lookang.streamlit.app/ from my own forked GitHub 
-  https://chergpt-physics-cpdd.streamlit.app/  from Kah How's deployment

## Features
- [x] Set custom instructions to guide student interactions.
- [WIP] Trigger immediate summaries of learning insights at the end of the session.

Need to secure access with a simple global password? Check the [authentication guide](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso).

## Use Cases
Chergpt-Basic enables a variety of use cases, with the primary one being the creation of user personas for students to interact with. Examples include historical figures or patients with specific medical conditions and a guided escape room for primary school Chinese Language Learning (wiht particular tasks as checks for understanding)

# Deploying
There are three main steps:<br>
1 Setup your database <br>
2 Getting your OpenAI API Key (will soon move to another open source model) <br>
3 Deploy to the web via Streamlit <br>
##1 How to setup backend (database)
We recommend using **NeonDB**, start [here](https://console.neon.tech/) <br>

1. Go to this link, login and create your account.<br>
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/c4921ffc-15ec-48d2-a4ba-8dec02ef66c1)
<br>
2. Create a free project with Singapore as the region. Pick any project and database name you like. 
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/69ea2458-4a6f-4591-a791-d4a9c22fa389)
3. Click on the copy icon - this will give you your database (DB) connection String that allows you to store data persistently in CherGPT.<br>
Keep this somewhere safe, you will also need to use this shortly.

## OpenAI API Key
- See [here](https://teachertech.beehiiv.com/p/api-openai) if you're unsure how to create it.<br>
Keep this somewhere safe, you will also need to use this shortly.

##3 Deploying to Streamlit
1. Create a streamlit account [here](https://streamlit.io/)
## Secrets.toml File Structure
In the `secrets.toml` file, specify three items: you have to change it to your own

```
OPENAI_API_KEY = "sk-Co6R5h4RcT....................................." 
ADMIN_PASSWORD= "passwordyourchoice" 
DB_CONNECTION = "postgresql://chergpt:PGPASSWORD@some-details-based-on-connection-string.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" 
```
- Used to gate access for updating custom instructions.
- Refer to instructions above on **How to Set Up Backend** if unsure.

Feel free to explore and enhance the functionality of Chergpt-Basic according to your specific needs!
