from .stripe import Stripe
from .logging import logger

stripe: Stripe = Stripe()
if stripe.api_key.startswith("sk_live_"):
    credits_product = 'prod_F4FUzg5Mp0HjsJ'
else:
    credits_product = 'prod_Eb12aVhUd70A4a'


def make_request(req, fields=[], params={}):
    result = []
    response = req(fields=fields, params=params, pending=True).execute()
    for item in response:
        if isinstance(response.params, list):
            response.params = {}
        result.append(item.export_all_data())
    return result


def get_available_billing_plans():
    skus = stripe.SKU.list(product=credits_product)

    return [
        {
            'name': f"package_{int(sku['attributes']['credits'])}",
            'credits': int(sku['attributes']['credits']),
            'price_cents': int(sku['price']),
            'id': sku['id']
        } for sku in skus['data']
    ]


def get_customer(email):
    try:
        matching_customers = stripe.Customer.list(limit=1, email=email)
        return stripe.Customer.construct_from(
            matching_customers['data'][0], stripe.api_key)
    except Exception as e:
        logger.exception(f'Raised an Error: {e}')
        return None
