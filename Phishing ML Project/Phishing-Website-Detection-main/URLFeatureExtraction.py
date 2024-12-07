import streamlit as st
import numpy as np
import pickle
from urllib.parse import urlparse
import requests
import re
import ipaddress


def get_domain(url):  
    domain = urlparse(url).netloc
    if re.match(r"^www.", domain):
        domain = domain.replace("www.", "")
    return domain

def having_ip(url):
    try:
        ipaddress.ip_address(url)
        return 1
    except ValueError:  # Handle invalid IP addresses
        return 0

def have_at_sign(url):
    return 1 if "@" in url else 0

def get_length(url):
    return 0 if len(url) < 54 else 1

def get_depth(url):
    s = urlparse(url).path.split('/')
    depth = sum(1 for j in s if len(j) != 0)
    return depth

def redirection(url):
    pos = url.rfind('//')
    if pos > 6:
        return 1 if pos > 7 else 0
    return 0

def http_domain(url):
    scheme = urlparse(url).scheme
    return 0 if scheme == 'https' else 1  # 0 for HTTPS, 1 for HTTP/other

def tiny_url(url):
    shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                          r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                          r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                          r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                          r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                          r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                          r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                          r"tr\.im|link\.zip\.net"
    return 1 if re.search(shortening_services, url) else 0

def prefix_suffix(url):
    return 1 if '-' in urlparse(url).netloc else 0 

def web_traffic(url):
    try:
        querystring = {"domain": url}
        headers = {
            "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",  # Replace with your actual API key
            "X-RapidAPI-Host": "similar-web.p.rapidapi.com"
        }
        response = requests.get("https://similar-web.p.rapidapi.com/get-analysis", headers=headers, params=querystring)
        data = response.json()

        # Safeguard if 'GlobalRank' or 'Rank' keys are missing
        rank = data.get('GlobalRank', {}).get('Rank', None)

        if rank is None:  # Handle None value
            rank = 100001  # Assign a value above the threshold for safe URLs

        return 1 if int(rank) < 100000 else 0

    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        st.error(f"Error retrieving web traffic data: {e}")
        return 1  # Fallback value if there's an exception

def iframe(response):
    if response == "":
        return 1
    return 0 if re.findall(r"[<iframe>|<frameBorder>]", response.text) else 1

def mouse_over(response): 
    if response == "":
        return 1
    return 1 if re.findall("<script>.+onmouseover.+</script>", response.text) else 0

def right_click(response):
    if response == "":
        return 1
    return 0 if re.findall(r"event.button ?== ?2", response.text) else 1

def forwarding(response):
    if response == "":
        return 1
    return 0 if len(response.history) <= 2 else 1

def get_http_response(url, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
            return response
        except requests.exceptions.Timeout:
            st.warning(f"Attempt {attempt + 1} of {retries}: Timeout occurred. Retrying...")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")
            return None  # Return None if there's a non-timeout error
    st.error("Failed to retrieve the URL after multiple attempts.")
    return None  # Return None if all attempts fail

def extract_features(url):
    features = []
    
    # Address bar based features
    features.append(having_ip(url))
    features.append(have_at_sign(url))
    features.append(get_length(url))
    features.append(get_depth(url))
    features.append(redirection(url))
    features.append(http_domain(url))
    features.append(tiny_url(url))
    features.append(prefix_suffix(url))

    # Domain based features (placeholders for DNS-related features)
    dns = 0
    dns_age = 0
    dns_end = 0
    features.append(dns)
    features.append(dns_age)
    features.append(dns_end)
    features.append(web_traffic(url))  # Updated to handle None case
    response = get_http_response(url)

    # HTML & Javascript based features
    if response is not None:
        features.append(iframe(response))
        features.append(mouse_over(response))
        features.append(right_click(response))
        features.append(forwarding(response))
    else:
        features.extend([0, 0, 0, 0])  # Set to 0 if no response

    return features

def predict_phishing(features):
    # Load the model
    with open('mlp_model.pkl', 'rb') as file:
        loaded_model = pickle.load(file)

    # Make predictions
    new_data = np.array([features])
    prediction = loaded_model.predict(new_data)

    return prediction

def main():
    st.title('Phishing URL Detector')
    st.write("Enter a URL to check if it's phishing or not.")
    
    # Input URL
    url = st.text_input("Enter URL:")
    
    if st.button("Check"):
        # Extract features
        st.write("Extracting features...")
        features = extract_features(url)

        # Make prediction
        st.write("Predicting...")
        prediction = predict_phishing(features)
        
        # Display prediction
        if prediction[0] == 0:
            st.error("Phishing Alert! This URL is classified as phishing.")
        else:
            st.success("No Phishing Detected. This URL seems safe.")
    
if __name__ == '__main__':
    main()
