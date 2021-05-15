import os
import stripe

from .logging import logger


class Stripe:
    stripe_key = os.environ['STRIPE_KEY']
    stripe_api_version = '2018-11-08'

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
