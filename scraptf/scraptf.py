import requests
from structlog import get_logger

GET_DONATIONS_ENDPOINT = 'https://dev.scrap.tf/api/fundraisers/getdonations.php'

log = get_logger()


# TODO: the logging story here is not great
class ScrapTF:
    """
    ScrapTF is used to interact with the Scrap.TF private API.
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def get_latest_donations(self, fundraiser, after=None, count=None):
        """
        get_latest_donations returns the latest donations for the given
        fundraiser.

        * after (datetime): limits to donations made after this time
        * count (int): limits to this many donations in the response
        """
        payload = {'key': self.api_key,
                   'fundraiser': fundraiser}
        if after:
            payload['confirmed_after'] = after.strftime('%s')

        if count:
            payload['num'] = count

        r = requests.post(GET_DONATIONS_ENDPOINT, params=payload)

        try:
            resp = r.json()
        except ValueError:
            log.critical('Failed to convert response to JSON.')
            return []

        if not resp['success']:
            log.critical('API request did not succeed.',
                         resp=resp)
            return []

        log.debug('Response info',
                  count=resp['count'],
                  latest_donation=resp['latest_donation'])

        return resp['donations']
