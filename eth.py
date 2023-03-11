import os
import aiohttp
import asyncio
import json
import requests
from web3 import AsyncWeb3, AsyncHTTPProvider

w3 = AsyncWeb3(AsyncHTTPProvider("https://rpc.ankr.com/eth"))

TX_COUNT = 10


async def get_safe_block_number():
    return await w3.eth.block_number


async def block_query(num):
    txs = []
    # tx types: 0: transfer, 1: deploy, 2: interaction

    if num:
        b = await w3.eth.get_block(num)
    else:
        b = await w3.eth.get_block("safe")

    for result in asyncio.as_completed(
        [w3.eth.get_transaction(tx_hash) for tx_hash in b.transactions[:TX_COUNT]]
    ):
        t = await result
        tx = {
            "block_number": t["blockNumber"],
            "hash": t["hash"].hex(),
            "to": t["to"],
            "from": t["from"],
            "value": t["value"],
            "input": t["input"],
            "function_sig": None,
            "decoded_inputs": None,
            "sourcify": None,
        }

        try:
            print(f"\nTx: {t.transactionIndex}")
        except:
            print("couldnt get transaction index")
            break

        # CONTRACT DEPLOYMENT:
        if tx["to"] is None:
            tx["type"] = 1
        # ETHER TRANSFER:
        elif tx["input"] == "0x":
            tx["type"] = 0
        # CONTRACT INTERACTION:
        else:
            tx["type"] = 2

            # SOURCIFY METADATA LOOKUP:
            url = f"https://sourcify.dev/server/repository/contracts/full_match/1/{t['to']}/metadata.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 404:
                        print(f"(Contract not found in sourcify)")
                    else:
                        data = await resp.read()
                        contract_data = json.loads(data)

                        target = contract_data["settings"]["compilationTarget"]
                        contract_name = list(target.values())[0]
                        abi = contract_data["output"]["abi"]
                        devdoc = contract_data["output"]["devdoc"]["methods"]

                        contract = w3.eth.contract(address=t["to"], abi=abi)
                        decoded_input = contract.decode_function_input(t["input"])
                        function_sig = str(decoded_input[0])[10:-1]

                        tx["function_sig"] = function_sig
                        tx["decoded_inputs"] = decoded_input[1]
                        tx["sourcify"] = contract_data
        txs.append(tx)

    return b, txs
