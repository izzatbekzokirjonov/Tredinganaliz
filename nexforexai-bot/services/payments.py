"""Builds Telegram Bot Payments invoices for plan upgrades.

Requires a payment provider token connected via @BotFather -> Payments
(e.g. Payme, Click, or Stripe depending on your region/currency).
"""

from aiogram.types import LabeledPrice

from config import PLAN_PRICES_USD, PAYMENT_PROVIDER_TOKEN

PLAN_DURATION_DAYS = 30


def build_invoice_params(plan: str) -> dict:
    """Returns kwargs ready to pass into bot.send_invoice(...)."""
    if plan not in PLAN_PRICES_USD:
        raise ValueError(f"Unknown plan: {plan}")

    price_usd = PLAN_PRICES_USD[plan]
    amount_cents = int(round(price_usd * 100))

    return {
        "title": f"NexForexAI {plan.capitalize()} - {PLAN_DURATION_DAYS} kun",
        "description": (
            f"{plan.capitalize()} rejasi {PLAN_DURATION_DAYS} kunga faollashadi. "
            f"Kunlik signal limiti oshiriladi."
        ),
        "payload": f"plan:{plan}:{PLAN_DURATION_DAYS}",
        "provider_token": PAYMENT_PROVIDER_TOKEN,
        "currency": "USD",
        "prices": [LabeledPrice(label=f"{plan.capitalize()} - {PLAN_DURATION_DAYS} kun", amount=amount_cents)],
    }


def parse_payload(payload: str) -> tuple[str, int]:
    """payload format: 'plan:<name>:<days>'"""
    _, plan, days = payload.split(":")
    return plan, int(days)
