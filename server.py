import os
import asyncio
import pickle
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from eth import block_query

loop = asyncio.get_event_loop()

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:///{os.path.join(basedir, 'data.sqlite')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)


#  block = {
#  "baseFeePerGas": 19305055585,
#  "difficulty": 0,
#  "extraData": HexBytes("0x6265617665726275696c642e6f7267"),
#  "gasLimit": 30000000,
#  "gasUsed": 9786685,
#  "hash": HexBytes(
#  "0x2f831297ced74e846a57e614547f5004bacd9119e2f3c9d0098d509e154b1cb6"
#  ),
#  "logsBloom": HexBytes(
#  "0xd4b0c544e1158080301d0159ac51132137e504045a804a442a09a1415c2911409606511820231882e4023f0a0063c15013ea48008e02a8048a45302001ec12204006e1905204282ced8a6628360040e00081003004c418402850174bb046e0109e65b0201a13e488020c2a00840028492a002304304a6c2126000092046ce2066d01d63d134a0802284184463181f405040010698120b4d86627ce68063b9810af1b19199306e10622436be0084b040000a40a204992228280233c13509e11051457205a1800185280402422024f0806c4a812e01007d0908a132926302060596078a2080102154c0b0c1783c2a1043583a541881898165306398112a40070c0"
#  ),
#  "miner": "0x95222290DD7278Aa3Ddd389Cc1E1d165CC4BAfe5",
#  "mixHash": HexBytes(
#  "0x6045ac46f864d1c4b50d6f0d0e829ef0d62a52acfae52b2f0b67e0c6edbc6c60"
#  ),
#  "nonce": HexBytes("0x0000000000000000"),
#  "number": 16878717,
#  "parentHash": HexBytes(
#  "0x092c1ebf0728c8f983466a6f552fe140f63c9368753d89be08a862c135ade0a1"
#  ),
#  "receiptsRoot": HexBytes(
#  "0x42683ceae3542d5ed8e87666fe309edf5a67586afb78c10197defbf983990dc6"
#  ),
#  "sha3Uncles": HexBytes(
#  "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
#  ),
#  "size": 38080,
#  "stateRoot": HexBytes(
#  "0x9adb261fabd05e79ad738e2c3d86ca2a5e402216e9f1d0f19117b5b5d26055e1"
#  ),
#  "timestamp": 1679434583,
#  "totalDifficulty": 58750003716598352816469,
#  "transactions": [],
#  "uncles": [],
#  }


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
    # edge cases to sort:
    #   16881111: devdoc no function_sig
    block = fetch_block(16881114)
    return render_template("txs.html", block_num=block.number, txs=block.txs.all())


@app.route("/tx/<int:block_num>")
def block(block_num):
    block = fetch_block(block_num)
    return render_template("txs.html", block_num=block.number, txs=block.txs.all())


def fetch_block(block_num):
    b = Block.query.filter_by(number=block_num).first()

    if b is None:
        print(f"∆∆∆ fetching new block")
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
