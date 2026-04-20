import os
import tweepy
from core.token_service import get_valid_token
from logger import get_logger

logger = get_logger("Social_Agent_Tools")

def get_twitter_client(session_id: str):
    """
    Initializes a Tweepy client using the stored OAuth 2.0 token for the session.
    Automatically refreshes expired tokens.
    """
    token = get_valid_token(session_id, "twitter")
    if not token:
        logger.warning(f"No Twitter token found for session {session_id}")
        return None

    # Tweepy Client for v2 API
    # Access token and Refresh token are in the token dict
    client = tweepy.Client(
        bearer_token=token.get("access_token"),
        consumer_key=os.getenv("TWITTER_CLIENT_ID"),
        consumer_secret=os.getenv("TWITTER_CLIENT_SECRET"),
        access_token=token.get("access_token"),
        access_token_secret=None, # Not used in OAuth 2.0 User Context
        wait_on_rate_limit=True
    )
    return client

def post_tweet(session_id: str, text: str):
    """
    Posts a tweet on behalf of the user.
    """
    client = get_twitter_client(session_id)
    if not client:
        return {
            "error": "Twitter account not connected",
            "a2ui": {
                "component": "A2Card",
                "title": "Connect X (Twitter)",
                "children": [
                    {
                        "component": "A2Text",
                        "value": "You haven't connected your X account yet. Connect it now to post tweets directly from this chat."
                    },
                    {
                        "component": "A2Button",
                        "label": "Connect X",
                        "type": "primary",
                        "on_click": "auth:login?provider=twitter"
                    }
                ]
            }
        }

    try:
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        return {
            "success": True,
            "tweet_id": tweet_id,
            "message": "Tweet posted successfully!",
            "a2ui": {
                "component": "A2Card",
                "title": "Tweet Posted",
                "type": "success",
                "children": [
                    {
                        "component": "A2Text",
                        "value": f"Successfully posted to X: \"{text}\""
                    },
                    {
                        "component": "A2Button",
                        "label": "View Tweet",
                        "url": f"https://twitter.com/i/web/status/{tweet_id}"
                    }
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        return {"error": f"Failed to post tweet: {str(e)}"}

def get_twitter_profile(session_id: str):
    """
    Fetches the authenticated user's profile info.
    """
    client = get_twitter_client(session_id)
    if not client:
        return {"error": "Twitter account not connected"}

    try:
        me = client.get_me(user_auth=False)
        user_data = me.data
        return {
            "username": user_data.username,
            "name": user_data.name,
            "id": user_data.id,
            "a2ui": {
                "component": "A2Card",
                "title": "X Profile",
                "children": [
                    {
                        "component": "A2Text",
                        "value": f"Connected as @{user_data.username} ({user_data.name})"
                    }
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch Twitter profile: {e}")
        return {"error": str(e)}
