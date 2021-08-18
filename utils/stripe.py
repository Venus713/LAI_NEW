import os
import stripe

from .logging import logger


class Stripe:
    stripe_key = os.environ['STRIPE_KEY']
    stripe_api_version = '2018-11-08'

    if stripe_key.startswith("sk_live_"):
        credits_product = 'prod_F4FUzg5Mp0HjsJ'
    else:
        credits_product = 'prod_Eb12aVhUd70A4a'

    def setup_stripe(self):
        stripe.api_key = self.stripe_key
        stripe.api_version = self.stripe_api_version
        return stripe

    def get_customer(self, email):
        stripe = self.setup_stripe()
        try:
            matching_customers = stripe.Customer.list(limit=1, email=email)
            return stripe.Customer.construct_from(
                matching_customers['data'][0],
                stripe.api_key
            )
        except Exception as e:
            logger.error(f'error in stripe: {e}')
            return None

    def get_available_billing_plans(self):
        skus = stripe.SKU.list(product=self.credits_product)

        return [
            {
                'name': f"package_{int(sku['attributes']['credits'])}",
                'credits': int(sku['attributes']['credits']),
                'price_cents': int(sku['price']),
                'id': sku['id']
            } for sku in skus['data']
        ]
