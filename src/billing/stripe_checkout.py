import stripe

from src.config import settings

stripe.api_key = settings.stripe_secret_key


async def create_checkout_session(telegram_user_id: int, plan: str = "solo") -> str:
    """Create a Stripe Checkout session and return the session URL."""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Agent Qonto — plan {plan.capitalize()}",
                    },
                    "unit_amount": 990,
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }
        ],
        mode="subscription",
        metadata={
            "telegram_user_id": str(telegram_user_id),
            "plan": plan,
        },
        success_url=f"{settings.webhook_base_url}/billing/success",
        cancel_url=f"{settings.webhook_base_url}/billing/cancel",
    )
    return session.url
