import functions_framework
import firebase_admin
from firebase_admin import firestore, auth
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

@functions_framework.cloud_event
def on_user_create(cloud_event):
    """
    Cloud Function trigger for new user creation in Firebase Authentication.
    """
    db = firestore.client()

    try:
        # Get the user data from the Cloud Event
        user_data = cloud_event.data
        if not user_data:
            print("No user data in Cloud Event.")
            return

        uid = user_data.get("uid")
        email = user_data.get("email")

        if not uid:
            print("No UID in user data.")
            return

        print(f"New user created: UID={uid}, Email={email}")

        # 1. Create a new organization for this user
        # We will use the user's UID as a preliminary name,
        # and they can change it later.
        org_data = {
            'name': f"{email}'s Organization",
            'owner_uid': uid
        }
        
        # Add the new organization to the 'organizations' collection
        org_ref = db.collection('organizations').document()
        org_ref.set(org_data)
        
        print(f"Created new organization with ID: {org_ref.id}")

        # 2. Add this user to the 'users' subcollection of that new organization
        user_in_org_data = {
            'email': email,
            'role': 'owner' # The user who signs up is the owner
        }
        
        # Create the subcollection document
        user_ref = db.collection('organizations').document(org_ref.id).collection('users').document(uid)
        user_ref.set(user_in_org_data)
        
        print(f"Added user {uid} to organization {org_ref.id} as owner.")
        
        print("Function execution successful.")

    except Exception as e:
        print(f"Error processing new user {uid}: {e}")
        # Optionally, you could try to delete the auth user here to
        # allow them to retry, but that could be complex.
        # For now, we just log the error.
        print("Error: Could not create organization structure.")