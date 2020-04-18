# How to Run

1. Install anaconda
2. In terminal, navigate to this directory
3. Run `conda env create -n sentiment_analysis -f ./environment.yml`
4. Activate the environment by running `conda activate sentiment_analysis`
5. Run this command `python -m spacy download en_core_web_sm`
6. Type in terminal `set FLASK_APP=server.py`
7. Then run `flask run`

The server will start. First time will take long because the models have to be trained and saved.

### After server is running:

1. Open Postman
2. Send a POST request to the url at which server is running. Ex. http://127.0.0.1:5000/
3. The result will be returned as json
