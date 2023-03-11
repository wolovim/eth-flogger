## eth-flogger

_eth-flogger == Ethereum Flask Logger_

A smol Python app to demo:

-   asynchronously reading transactions from the Ethereum blockchain,
-   decoding transaction input,
-   fetching [Sourcify](https://sourcify.dev/) contract metadata,
-   storing data in a local (SQLite) database, and
-   displaying that data in a simple UI

<img src="https://i.imgur.com/zenUz3r.png" height="60%" width="60%" >

### Disclaimer

This app is for educational purposes and doesn't aspire to be anything production-worthy.
Error handling and retry logic are largely omitted; if you hit an exception, just try refreshing or searching for a specific block number.

You may find value in this repo as a jumping off point for a hackathon project, or just some patterns to reference, re: async web3.py, Sourcify, Flask, SQLite, SQLAlchemy, etc.

### Running locally

-   Install [poetry](https://python-poetry.org/docs/#installation)
-   Install eth-flogger dependencies: `poetry install`
-   Initialize the database:
    -   `export FLASK_APP=server.py`
    -   `flask db init`
    -   `flask db migrate -m "init"`
    -   `flask db upgrade`
-   Run the Flask server: `python server.py`
-   `open http://127.0.0.1:5000`
-   To view a specific block: `open http://127.0.0.1:5000/b/<block-number>`
