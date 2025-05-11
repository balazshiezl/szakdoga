from flask_wtf.csrf import CSRFProtect  # csak CSRFProtect import kell
from flask import Blueprint, jsonify, request, url_for, redirect, flash
from flask_login import login_required, current_user
from models.db import get_connection
import stripe
from extensions import csrf
import os
from dotenv import load_dotenv
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/create-checkout-session/<plan>', methods=['POST'])
@login_required
def create_checkout_session(plan):
    price_lookup = {
        'halado': 'price_1R8I2DR7HJHOCBgm532K337H',
        'profi': 'price_1R8I4sR7HJHOCBgmDtA05EGP'
    }

    price_id = price_lookup.get(plan)
    if not price_id:
        return jsonify({'error': 'Érvénytelen csomag típus'}), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('user.dashboard', _external=True),
            cancel_url=url_for('user.dashboard', _external=True),
            customer_email=current_user.email,
            metadata={"plan": plan}
        )
        return jsonify({'id': session.id})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify(error=str(e)), 500


@csrf.exempt
@subscription_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError as e:
        print("[Webhook] Signature verification failed:", e)
        return '', 400
    except Exception as e:
        print("[Webhook] General webhook error:", e)
        return '', 400

    print("[Webhook] Event type:", event['type'])  # <<< LOG
    print("[Webhook] Event data:", event['data'])  # <<< LOG

    if event['type'] in ['checkout.session.completed', 'invoice.paid']:
        session = event['data']['object']

        email = session.get('customer_email')
        plan = None

        if 'metadata' in session and session['metadata'].get('plan'):
            plan = session['metadata']['plan']

        # Ha nincs email, próbáljuk a customer ID alapján lekérni
        if not email and session.get('customer'):
            try:
                customer = stripe.Customer.retrieve(session['customer'])
                email = customer.get('email')
            except Exception as e:
                print("[Webhook] Nem sikerült lekérni a Stripe customert:", e)

        # Ha invoice.paid és nincs plan, próbáljuk a subscriptionból
        if not plan and session.get('subscription'):
            try:
                subscription = stripe.Subscription.retrieve(session['subscription'])
                price = subscription['items']['data'][0]['price']
                plan = price['nickname'].lower()  # helyesen nickname-ből
            except Exception as sub_error:
                print("[Webhook] Hiba a subscription lekérdezés közben:", sub_error)

        # Most, hogy van email és plan
        if email and plan:
            try:
                conn = get_connection()
                conn.run(
                    "UPDATE users SET is_subscribed = TRUE, subscription_plan = :plan WHERE email = :email",
                    plan=plan,
                    email=email
                )
                print(f"[Webhook] Sikeresen frissítve: email={email}, plan={plan}")
                conn.close()
            except Exception as db_error:
                print("[Webhook] Adatbázis hiba:", db_error)
                return '', 500
        else:
            print(f"[Webhook] Hiányos adatok: email={email}, plan={plan}")

    return '', 200




@subscription_bp.route('/cancel_subscription', methods=['POST'])
@login_required
def cancel_subscription():
    try:
        conn = get_connection()
        conn.run("UPDATE users SET is_subscribed = FALSE, subscription_plan = NULL WHERE id = :id", id=current_user.id)
        conn.close()

        flash("Előfizetés lemondva.", "success")
    except Exception as e:
        print("Lemondás hiba:", e)
        flash("Nem sikerült lemondani az előfizetést.", "error")

    return redirect(url_for('user.dashboard'))

