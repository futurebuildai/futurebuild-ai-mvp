import firebase_admin
from firebase_admin import auth, firestore
from functions_framework import cloudevent

# Initialize the Firebase Admin SDK. This is done once when the function starts.
# The SDK will automatically use the project's default credentials.
firebase_admin.initialize_app()

@cloudevent
def on_user_create(cloud_event):
    """
    A CloudEvent function that triggers when a new Firebase Authentication
    user is created.
    """
    # Extract the user's data from the trigger event
    event_data = cloud_event.data["protoPayload"]["resourceName"]
    
    # The user's UID is the last part of the resourceName string
    # Example: "projects/futurebuild-ai-mvp/users/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    uid = event_data.split('/')[-1]

    try:
        # Get the full user record from Firebase Authentication
        user = auth.get_user(uid)
        print(f"New user created: UID={user.uid}, Email={user.email}")

        # Get a reference to the Firestore database
        db = firestore.client()

        # Create a new document in the 'users' collection
        user_doc_ref = db.collection('users').document(user.uid)
        user_doc_ref.set({
            'email': user.email,
            'displayName': user.display_name,
            'creation_timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"Successfully created user document for UID: {user.uid}")

        # Create a new 'organization' for this user
        # This establishes the "organization of one" for the new user
        org_doc_ref = db.collection('organizations').document()
        org_doc_ref.set({
            'name': f"{user.email}'s Organization",
            'owner_uid': user.uid,
            'creation_timestamp': firestore.SERVER_TIMESTAMP,
            'members': {
                user.uid: 'owner' # The 'members' map is key to our security rules
            }
        })
        print(f"Successfully created organization for user: {user.uid}")

    except Exception as e:
        print(f"Error processing new user {uid}: {e}")