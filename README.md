# chergpt-basic: custom chat assistant
No login, vanilla ChatGPT-like interface with scaffolded code for immediate deployment 

## Features
- [x] Set custom instructions to guide student interactions <br>
- [WIP] Trigger immediate summaries of learning insights at the end of the session <br>

Need to gate access with a simple global password? See [here](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso) 

## Use cases
The most straightforward use of custom instructions is to create user personas for students to interact with. <br>
E.g. historical figures, patients with particular medical conditions

## How to setup backend 
We recommend using **NeonDB** 
You can follow instructions on NeonDB [here](https://start.open.gov.sg/docs/getting-started/prerequisites) <br>

Your cluster will be created in a few seconds and the Create SQL user dialog will display.

For either (A) or (B), copy the URL and put it as `DB_CONNECTION = "{DB connection String}"` under `secrets.toml`

## secrets.toml file structure
You will need to specify 3 items:<br>
```
OPENAI_API_KEY = "{api_key}" #See [here](https://teachertech.beehiiv.com/p/api-openai) if you unsure on how to create<br>
DB_CONNECTION = "{db_connection string}" #Refer to instructions above on **How to setup backend** if unsure
ADMIN_PASSWORD = "{any password you want}" #This is used to gate access on how can update custom instructions
```

