"""Miner update functions"""
import sqlite3
import random

from .utils import get_last_block_hash
# from .p2p.outgoing import propogate_transaction_to_peers
from .p2p.utils import get_my_address
from ..constants import COMMITTEE_SIZE, IS_TEST, NEWRL_DB, TIME_MINER_BROADCAST_INTERVAL
from .auth.auth import get_wallet
from .signmanager import sign_transaction
from ..ntypes import TRANSACTION_MINER_ADDITION
from .utils import get_time_ms
from .transactionmanager import Transactionmanager
from .validator import validate


def miner_addition_transaction(wallet=None, my_address=None):
    if wallet is None:
        wallet = get_wallet()
    if my_address is None:
        my_address = get_my_address()
    timestamp = get_time_ms()
    transaction_data = {
        'timestamp': timestamp,
        'type': TRANSACTION_MINER_ADDITION,
        'currency': "NWRL",
        'fee': 0.0,
        'descr': "Miner addition",
        'valid': 1,
        'block_index': 0,
        'specific_data': {
            'wallet_address': wallet['address'],
            'network_address': my_address,
            'broadcast_timestamp': timestamp
        }
    }

    transaction_manager = Transactionmanager()
    transaction_data = {'transaction': transaction_data, 'signatures': []}
    transaction_manager.transactioncreator(transaction_data)
    transaction = transaction_manager.get_transaction_complete()
    signed_transaction = sign_transaction(wallet, transaction)
    return signed_transaction


def get_miner_status(wallet_address):
    con = sqlite3.connect(NEWRL_DB)
    cur = con.cursor()
    miner_cursor = cur.execute(
        'SELECT wallet_address, network_address, last_broadcast_timestamp FROM miners WHERE wallet_address=?', (wallet_address, )).fetchone()
    if miner_cursor is None:
        return None
    miner_info = {
        'wallet_address': miner_cursor[0],
        'network_address': miner_cursor[1],
        'broadcast_timestamp': miner_cursor[2]
    }
    return miner_info


def get_my_miner_status():
    wallet = get_wallet()
    my_status = get_miner_status(wallet['address'])
    return my_status


def broadcast_miner_update():
    transaction = miner_addition_transaction()
    validate(transaction)


def get_committee_list():
    last_block = get_last_block_hash()
    last_block_epoch = 0
    try:
        # Need try catch to support older block timestamps
        last_block_epoch = int(last_block['timestamp'])
    except:
        pass
    if last_block:
        cutfoff_epoch = last_block_epoch - TIME_MINER_BROADCAST_INTERVAL
    else:
        cutfoff_epoch = 0

    con = sqlite3.connect(NEWRL_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    miner_cursor = cur.execute(
        '''SELECT wallet_address, network_address, last_broadcast_timestamp 
        FROM miners 
        WHERE last_broadcast_timestamp > ?
        ORDER BY wallet_address ASC''', (cutfoff_epoch, )).fetchall()
    miners = [dict(m) for m in miner_cursor]
    con.close()
    return miners


def get_miner_for_current_block():
    last_block = get_last_block_hash()

    if not last_block:
        return

    random.seed(last_block['index'])

    committee_list = get_committee_list()

    return random.choice(committee_list)

    # return committee_list[0]


def get_committee_for_current_block():
    last_block = get_last_block_hash()

    if not last_block:
        return

    random.seed(last_block['index'])

    miners = get_committee_list()
    committee_size = min(COMMITTEE_SIZE, len(miners))
    committee = random.sample(miners, k=committee_size)
    return committee


def should_i_mine():
    my_wallet = get_wallet()
    miner = get_miner_for_current_block()
    if miner['wallet_address'] == my_wallet['address']:
        return True
    return False


def am_i_in_current_committee():
    my_wallet_address = get_wallet()['address']
    committee = get_committee_for_current_block()

    found = list(filter(lambda w: w['wallet_address'] == my_wallet_address, committee))
    if len(found) == 0:
        return False
    return True