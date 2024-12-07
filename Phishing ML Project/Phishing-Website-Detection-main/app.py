import streamlit as st
import numpy as np
import pickle
from urllib.parse import urlparse
import requests
import re
import ipaddress

# Function to toggle theme
def toggle_theme():
    if st.session_state.get("dark_mode", False):
        st.session_state.dark_mode = False
        st.markdown(
            """
            <style>
            .stApp {
                background-color: white; /* Light background */
                color: black; /* Text color */
            }
            .btn {
                background-color: #007bff; /* Bootstrap primary color */
                color: white; /* Button text color */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }
            .btn:hover {
                background-color: #0056b3; /* Darker shade on hover */
            }
            h1, h2, h3, h4, h5, h6 {
                color: black; /* Header colors in light mode */
            }
            p, div, span {
                color: black; /* General text color in light mode */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.session_state.dark_mode = True
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #1e1e1e; /* Dark background */
                color: rgba(255, 255, 255, 1); /* Fully opaque white text */
            }
            .btn {
                background-color: #007bff; /* Blue button for dark mode */
                color: white; /* Button text color */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }
            .btn:hover {
                background-color: #0056b3; /* Darker shade on hover */
            }
            h1, h2, h3, h4, h5, h6 {
                color: rgba(255, 255, 255, 1); /* Fully opaque white headers */
            }
            p, div, span {
                color: rgba(255, 255, 255, 0.9); /* High opacity for general text */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

def preprocess_url(url):
    # Check if the URL starts with http:// or https://
    if not re.match(r'^https?://', url):
        # If not, prepend http:// to the URL
        url = 'http://' + url
    return url

def get_domain(url):  
    domain = urlparse(url).netloc
    if re.match(r"^www.", domain):
        domain = domain.replace("www.", "")
    return domain

def having_ip(url):
    try:
        ipaddress.ip_address(urlparse(url).netloc)
        return 1
    except:
        return 0

def have_at_sign(url):
    return 1 if "@" in url else 0

def get_length(url):
    return 0 if len(url) < 54 else 1

def get_depth(url):
    s = urlparse(url).path.split('/')
    return sum(1 for segment in s if len(segment) != 0)

def redirection(url):
    pos = url.rfind('//')
    return 1 if pos > 6 and pos > 7 else 0

def http_domain(url):
    # Check if the URL uses 'https'
    scheme = urlparse(url).scheme
    return 0 if scheme == 'https' else 1  # Return 1 for HTTP or anything else

def tiny_url(url):
    shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                          r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                          r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                          r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                          r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                          r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                          r"prettylinkpro\.com|scrnch\.me|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                          r"tr\.im|link\.zip\.net"
    match = re.search(shortening_services, url)
    return 1 if match else 0

def prefix_suffix(url):
    return 1 if '-' in urlparse(url).netloc else 0 

def web_traffic(url):
    try:
        querystring = {"domain": url}
        headers = {
            "X-RapidAPI-Key": "cd4733fedbmsh6f2cfc21cf195f2p1d088djsn84e6c824c74e",
            "X-RapidAPI-Host": "similar-web.p.rapidapi.com"
        }
        response = requests.get("https://similar-web.p.rapidapi.com/get-analysis", headers=headers, params=querystring)
        data = response.json()
        rank = data['GlobalRank']['Rank']
        return 1 if int(rank) < 100000 else 0
    except (requests.exceptions.RequestException, ValueError, KeyError):
        return 1  # Return 1 if there was an error accessing the traffic data

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

def get_http_response(url):
    try:
        response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Error accessing the URL '{url}': {str(e)}")
        return None

def extract_features(url):
    features = []
    
    # Address bar based features
    features.append(having_ip(url))
    features.append(have_at_sign(url))
    features.append(get_length(url))
    features.append(get_depth(url))
    features.append(redirection(url))
    features.append(http_domain(url))  # This now checks HTTP vs HTTPS
    features.append(tiny_url(url))
    features.append(prefix_suffix(url))

    # Domain based features
    dns = 0  # Placeholder for DNS feature
    dns_age = 0  # Placeholder for DNS age feature
    dns_end = 0  # Placeholder for DNS end feature
    features.append(dns)
    features.append(dns_age)
    features.append(dns_end)
    features.append(web_traffic(url))
    response = get_http_response(url)

    # HTML & Javascript based features
    if response is not None:
        features.append(iframe(response))
        features.append(mouse_over(response))
        features.append(right_click(response))
        features.append(forwarding(response))
    else:
        # If response is None, set these features to 0
        features.extend([0, 0, 0, 0])

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

    # Theme toggle button
    if 'dark_mode' not in st.session_state:A
        st.session_state.dark_mode = False

    if st.button("Toggle Dark/Light Theme"):
        toggle_theme()

    st.write("Enter a URL to check if it's phishing or not.")
    
    # Input URL
    url = st.text_input("Enter URL:")
    
    if st.button("Check"):
        # Preprocess the URL
        processed_url = preprocess_url(url)

        # Validate URL for HTTPS and .com or .net
        if not re.match(r'^https://.*\.(com|net)$', processed_url):
            st.error("Phishing Alert! This URL is considered phishing (must be HTTPS and end with .com or .net).")
            return

        # Extract features
        st.write("Extracting features...")
        features = extract_features(processed_url)

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
