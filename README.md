# chergpt-basic: custom chat assistant
No login, vanilla ChatGPT-like interface with scaffolded code for immediate deployment 

<img width="1283" alt="image" src="https://github.com/String-sg/chergpt-basic/assets/44336310/5be6253c-5de6-402a-8d47-b37c52154d65">

## Features
- [x] Set custom instructions to guide student interactions <br>
- [WIP] Trigger immediate summaries of learning insights at the end of the session <br>

Need to gate access with a simple global password? See [here](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso) 

# How to get backend 
A) **NeonDB** You can follow instructions on NeonDB here: https://start.open.gov.sg/docs/getting-started/prerequisites
B) **CockroachDB** <br>
Create a CockroachDB Serverless cluster (free)<br>
Sign up for a CockroachDB Cloud account.<br>
Log in to your CockroachDB Cloud account.<br>
On the Clusters page, click Create Cluster.<br>
On the Create your cluster page, select Serverless.<br>
Click Create cluster.<br>

Your cluster will be created in a few seconds and the Create SQL user dialog will display.

For either (A) or (B), copy the URL and put it as `DB_CONNECTION = "{DB connection String}"` under `secrets.toml`
