# Chergpt-Basic: Custom Chat Assistant
Chergpt-Basic is a simplified, login-free ChatGPT-like interface designed for quick deployment
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/7781fef9-7954-4a47-9523-0edb200b48c0)
It is also mobile friendly! <br>
<img src="https://github.com/String-sg/chergpt-basic/assets/44336310/f21a155a-75a2-4ab5-be5f-95c25ca5c2d9" width="200" />

## Deployment - examples
-  https://chergpt-physics-lookang.streamlit.app/ from my own forked GitHub 
-  https://chergpt-physics-cpdd.streamlit.app/  from Kah How's deployment

## Features
- [x] Set custom instructions to guide student interactions.
- [x] Download chatlogs
- [x] Generate learning/ teaching analytics based on chatlogs

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
2. Create a free project with Singapore as the region. Pick any project and database name you like. <br>
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/c5e529e2-74c6-47d8-935e-43b0a911c252)

![image](https://github.com/String-sg/chergpt-basic/assets/44336310/f5a3f4f3-dfb1-440d-959b-d71c5a6b00e2)
<br>
3. Click on the copy icon - this will give you your database (DB) connection String that allows you to store data persistently in CherGPT.<br>
Keep this somewhere safe, you will also need to use this shortly.

## OpenAI API Key
- See [here](https://teachertech.beehiiv.com/p/api-openai) if you're unsure how to create it.<br>
Keep this somewhere safe, you will also need to use this shortly.

## 3 Deploying to Streamlit

# Click [here](https://share.streamlit.io/create-from-fork?owner=string-sg&repository=chergpt-basic&branch=main&mainModule=main.py&appId=c730ddec-3987-442a-9ed0-14754a284ed0)

1. You will be prompted to create a streamlit account [here](https://streamlit.io/)
2. You will be prompted to create a github account
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/f6db1538-2481-4cd8-95e0-a45a02285768)
3. You should see this screen - edit the domain to anything of your choice!
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/8574e485-06fb-4b0c-b7d9-48755ce7bc8d)
4. Go to advanced settings and update Secrets.toml with your own values
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/114583ab-a36e-4725-8d65-3705393293a3)
5. Upon clicking "fork", wait a few mins:<br>
![image](https://github.com/String-sg/chergpt-basic/assets/44336310/6270480b-0e97-4195-815f-5f9b7e2939fd)


Feel free to explore and enhance the functionality of Chergpt-Basic according to your specific needs!
