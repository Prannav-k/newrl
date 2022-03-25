import requests
from threading import Thread

from ..minermanager import get_committee_for_current_block
from ...constants import IS_TEST, NEWRL_PORT, REQUEST_TIMEOUT, TRANSPORT_SERVER
from ..p2p.utils import get_peers
from ..p2p.utils import is_my_address


def propogate_transaction_to_peers(transaction):
    if IS_TEST:
        return
    peers = get_peers()
        
    for peer in peers:
        if is_my_address(peer['address']):
            continue
        url = 'http://' + peer['address'] + ':' + str(NEWRL_PORT)
        print('Broadcasting transaction to peer', url)
        payload = {'signed_transaction': transaction}
        try:
            thread = Thread(target=send_request, args = (url + '/receive-transaction', payload))
            thread.start()
        except Exception as e:
            print(f'Error broadcasting block to peer: {url}')
            print(e)

def send_request_in_thread(url, data):
    thread = Thread(target=send_request, args = (url, data))
    thread.start()

def send_request(url, data):
    if IS_TEST:
        return
    try:
        requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f'Could not send request to node {url}')

def send(payload):
    response = requests.post(TRANSPORT_SERVER + '/send', json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        print('Error sending')
    return response.text


def broadcast_receipt(receipt):
    if IS_TEST:
        return
    committee = get_committee_for_current_block()

    for peer in committee:
        if is_my_address(peer['network_address']):
            continue
        url = 'http://' + peer['network_address'] + ':' + str(NEWRL_PORT)
        print('Broadcasting transaction to peer', url)
        payload = {'receipt': receipt}
        try:
            thread = Thread(target=send_request, args=(url + '/receive-receipt', payload))
            thread.start()
        except Exception as e:
            print(f'Error broadcasting receipt to peer: {url}')
            print(e)

