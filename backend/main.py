import firebase_admin
import datetime
import functions_framework
from firebase_admin import firestore
from google.cloud.firestore import Client

# Initialize Firebase Admin SDK
# This is done once when the function instance starts.
firebase_admin.initialize_app()

# This is a generic CloudEvent function.
# It will be triggered by the event specified in our gcloud deploy command.
@functions_framework.cloud_event
def on_user_create_function_gen1(cloud_event):
    """
    Triggered by the legacy 'providers/firebase.auth/eventTypes/user.create' event.
    
    This function creates a new 'organization' document in Firestore and
    adds the new user to a 'users' subcollection within that organization
    as the 'owner'.
    """
    try:
        # The user data payload is in the 'data' attribute of the cloud_event
        # This part is a "best guess" based on the legacy trigger.
        # If it fails, the logs will show us the *actual* structure.
        if not cloud_event.data:
            print("No data found in cloud_event. Exiting.")
            return

        payload = cloud_event.data
        
        # We must now parse this payload. We *assume* it has 'uid' and 'email'.
        # This is the part that will likely fail and need debugging (as expected).
        uid = payload.get('uid')
        email = payload.get('email')

        if not uid or not email:
            print(f"CloudEvent data payload is missing 'uid' or 'email'.")
            print(f"Payload received: {payload}")
            return

        print(f"Processing new user: UID {uid}, Email {email}")

        # Get the Firestore client
        db: Client = firestore.client()

        # 1. Create a new organization document
        org_ref = db.collection('organizations').document()
        org_id = org_ref.id
        
        org_name = "My First Organization"
        
        org_data = {
            'org_name': org_name,
            'created_at': datetime.datetime.now(datetime.timezone.utc),
            'org_id': org_id
        }
        
        org_ref.set(org_data)
        print(f"Successfully created organization {org_id} with name '{org_name}'")

        # 2. Add the new user to the 'users' subcollection
        user_ref = org_ref.collection('users').document(uid)
        
        user_data_for_org = {
            'email': email,
            'role': 'owner',
            'joined_at': datetime.datetime.now(datetime.timezone.utc)
        }
        
        user_ref.set(user_data_for_org)
        
        print(f"Successfully added user {uid} as 'owner' to organization {org_id}")

    except Exception as e:
        # Log any errors that occur during execution.
        print(f"Error processing new user: {e}")
        # We also print the event data to help debug payload structure issues
        print(f"Full event data: {cloud_event.data}")
        raise