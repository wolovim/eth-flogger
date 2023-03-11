import os
import asyncio
import pickle
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from eth import block_query, get_safe_block_number

loop = asyncio.get_event_loop()

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:///{os.path.join(basedir, 'data.sqlite')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)


class Block(db.Model):
    __tablename__ = "blocks"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    miner = db.Column(db.Text)
    gas_limit = db.Column(db.Integer)
    gas_used = db.Column(db.Integer)
    base_fee_per_gas = db.Column(db.Integer)
    timestamp = db.Column(db.Integer)
    txs = db.relationship("Tx", backref="block", lazy="dynamic")

    def __init__(self, block):
        self.number = block["number"]
        self.miner = block["miner"]
        self.gas_limit = block["gasLimit"]
        self.gas_used = block["gasUsed"]
        self.base_fee_per_gas = block["baseFeePerGas"]
        self.timestamp = block["timestamp"]


class Tx(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    block_number = db.Column(db.Integer, db.ForeignKey("blocks.number"))
    hash = db.Column(db.Text)
    to = db.Column(db.Text)
    from_ = db.Column(db.Text)
    value = db.Column(db.Integer)
    input = db.Column(db.Text)
    type = db.Column(db.Integer)
    function_sig = db.Column(db.String)
    decoded_inputs = db.Column(db.PickleType)
    sourcify = db.Column(db.PickleType)

    def __init__(self, tx):
        self.hash = tx["hash"]
        self.to = tx["to"]
        self.from_ = tx["from"]
        self.value = tx["value"]
        self.input = tx["input"]
        self.type = tx["type"]
        self.block_number = tx["block_number"]
        self.function_sig = tx["function_sig"]
        self.decoded_inputs = tx["decoded_inputs"]
        self.sourcify = tx["sourcify"]


@app.route("/")
def index():
    block = fetch_block()
    return render_template("txs.html", block_num=block.number, txs=block.txs.all())


@app.route("/b/<int:block_num>")
def block(block_num):
    block = fetch_block(block_num)
    return render_template("txs.html", block_num=block.number, txs=block.txs.all())


def fetch_block(block_num = None):
    if block_num is None:
        block_num = loop.run_until_complete(get_safe_block_number())

    b = Block.query.filter_by(number=block_num).first()

    if b is None:
        block, txs = loop.run_until_complete(block_query(block_num))
        blk = Block(block)

        txs_to_commit = []
        for tx in txs:
            t = Tx(tx)
            txs_to_commit.append(t)

        db.session.add(blk)
        db.session.add_all(txs_to_commit)
        db.session.commit()
        b = Block.query.filter_by(number=block_num).first()

    return b


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
