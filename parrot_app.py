import streamlit as st
from PIL import Image
import firebase_admin
from firebase_admin import credentials, storage, firestore, auth
import stripe
import uuid

# Initialize Firebase
cred = credentials.Certificate(st.secrets["FIREBASE_CREDENTIALS_JSON"])
firebase_admin.initialize_app(cred, {
    'storageBucket': f"{cred.project_id}.appspot.com"
})
db = firestore.client()
bucket = storage.bucket()

# Initialize Stripe
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

st.title("🦜 ParrotPal MVP")
st.sidebar.header("Account")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Sign Up"):
    try:
        user = auth.create_user(email=email, password=password)
        st.success("Signed up! Please log in now.")
    except Exception as e:
        st.error(str(e))

if st.sidebar.button("Log In"):
    try:
        user = auth.get_user_by_email(email)
        st.success(f"Logged in as {email}")
    except Exception as e:
        st.error(str(e))

# Upload video
st.header("Upload your parrot video")
uploaded_file = st.file_uploader("Choose video", type=["mp4", "mov", "avi"])
if uploaded_file:
    video_id = str(uuid.uuid4())
    blob = bucket.blob(f"videos/{video_id}.mp4")
    blob.upload_from_file(uploaded_file)
    db.collection("videos").document(video_id).set({
        "owner": email,
        "url": blob.public_url,
        "likes": 0,
        "comments": [],
    })
    st.success("Video uploaded!")

# Display feed
st.header("Video Feed")
videos = db.collection("videos").stream()
for vid in videos:
    v = vid.to_dict()
    st.video(v["url"])
    st.write(f"Owner: {v['owner']}")
    if st.button(f"Like {vid.id}"):
        db.collection("videos").document(vid.id).update({"likes": firestore.Increment(1)})
    st.write(f"Likes: {v['likes']}")
    comment = st.text_input(f"Comment for {vid.id}")
    if st.button(f"Add Comment {vid.id}") and comment:
        db.collection("videos").document(vid.id).update({"comments": firestore.ArrayUnion([comment])})
    st.write("Comments:", v["comments"])

# Donation
st.sidebar.header("Support creators 🌱")
amount = st.sidebar.number_input("Donate $", min_value=1, step=1)
if st.sidebar.button("Buy Me Seeds"):
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'usd','product_data': {'name': 'Buy Me Seeds'},'unit_amount': int(amount*100)}, 'quantity':1}],
        mode='payment',
        success_url="https://your-app-url/success",
        cancel_url="https://your-app-url/cancel",
    )
    st.sidebar.write(f
