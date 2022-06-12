import requests
import json


def format_str(obj):
    """
    :param datetime obj
    :return: "day/month/year"
    """
    return obj.strftime('%d/%m/%Y')


def get_total_usd():
    """
    Function to get usd price equivalent to argentina peso
    :param self
    :return: 0 if error get request or payload if success
    """
    try:
        response = requests.get('https://www.dolarsi.com/api/api.php?type=valoresprincipales')
        if response.status_code != 200:
            return 0
        else:
            payload = json.loads(json.dumps(response.json(), indent=4))
            result = {
                'casa': payload[0]['casa']['nombre'],
                'valor': payload[0]['casa']['compra'],
            }
            return result
    except Exception as ex:
        return ex.__str__()
