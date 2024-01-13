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
A) **NeonDB** You can follow instructions on NeonDB here: https://start.open.gov.sg/docs/getting-started/prerequisites <br>
B) **CockroachDB** <br>
* Create a CockroachDB Serverless cluster (free)<br>
* Sign up for a CockroachDB Cloud account.<br>
* Log in to your CockroachDB Cloud account.<br>
* On the Clusters page, click Create Cluster.<br>
* On the Create your cluster page, select Serverless.<br>
* Click Create cluster.<br>

Your cluster will be created in a few seconds and the Create SQL user dialog will display.

For either (A) or (B), copy the URL and put it as `DB_CONNECTION = "{DB connection String}"` under `secrets.toml`

## secrets.toml file structure
You will need to specify 3 items:
OPENAI_API_KEY = "{api_key}" #See (here)[https://teachertech.beehiiv.com/p/api-openai] if you unsure on how to create<br>
DB_CONNECTION = "{db_connection string}" #Refer to instructions above on **How to setup backend** if unsure<br>
ADMIN_PASSWORD = "{any password you want}" This is used to gate access on how can update custom instructions<br>
