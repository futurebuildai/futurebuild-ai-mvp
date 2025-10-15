import firebase_admin
from firebase_admin import auth, firestore
import functions_framework

# Initialize the Firebase Admin SDK.
firebase_admin.initialize_app()

# DEFINITIVE FIX #1: This HTTP function exists to satisfy the Gen2 health check.
@functions_framework.http
def on_user_create_http(request):
    """A simple HTTP function to pass the startup health check."""
    return "OK", 200

# DEFINITIVE FIX #2: The decorator is now correct (@functions_framework.cloud_event).
@functions_framework.cloud_event
def on_user_create_ce(cloud_event):
    """Triggers when a new Firebase Authentication user is created."""
    try:
        event_data = cloud_event.data["protoPayload"]["resourceName"]
        uid = event_data.split('/')[-1]

        user = auth.get_user(uid)
        print(f"New user created: UID={user.uid}, Email={user.email}")

        db = firestore.client()

        # Create user document
        user_doc_ref = db.collection('users').document(user.uid)
        user_doc_ref.set({
            'email': user.email,
            'displayName': user.display_name,
            'creation_timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"Successfully created user document for UID: {user.uid}")

        # Create organization document
        org_doc_ref = db.collection('organizations').document()
        org_doc_ref.set({
            'name': f"{user.email}'s Organization",
            'owner_uid': user.uid,
            'creation_timestamp': firestore.SERVER_TIMESTAMP,
            'members': {
                user.uid: 'owner'
            }
        })
        print(f"Successfully created organization for user: {user.uid}")

    except Exception as e:
        # Log any errors that occur during execution.
        print(f"Error processing new user {uid}: {e}")
        # Re-raise the exception to ensure the function fails visibly in the logs.
        raise