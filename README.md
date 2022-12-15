# The OAuth2 authorization code flow using FastAPI
This repository showcases two examples of how to implement the OAuth2 authorization code flow. The `basic` example contains the API routes needed to complete the OAuth2 authorization code flow. At the end, you'll be left with access and refresh tokens for the user and the scopes you requested. The `sessions` example expands on that with signed session cookies managed by `starlette`'s `SessionMiddleware`. These session cookies allow a client to authenticate using a cookie issued to them by your API service. Since the cookies are *signed*, you'll be able to verify if they have been tampered with (actually, `starlette` automatically does that for you, denying modified cookies a session and thus, authentication). This example then also showcases how to get the currently active user and how to restrict endpoints to logged-in users only.

The examples showcased here are built as concise and straight-to-the point as possible, foregoing return models (using `pydantic`) and other advanced FastAPI features to put the spotlight on the OAuth2 flow. I will highlight some more advanced concepts in the **Extending these examples** section.


# Prerequisites
* These examples were built and tested using Python 3.9.13, but they should also work for lower versions provided the libraries are available
* Install the dependencies listed in `requirements.txt`. If you intend to run the `basic` example, you don't need to install `aiohttp`. `starlette` will be installed with `fastapi`, but I included it for clarity. `httpx` and `itsdangerous` are needed by `authlib`. Finally, `uvicorn` is used to serve the app. I chose to include running the app in the respective main files for ease of demonstration, but you'll probably want to run the app from the command line using some variation of `$ uvicorn main:app` in a productive environment.
* Your OAuth2 flow will be rejected unless you have authorized the redirect URI you request the flow to be directed to after obtaining the authorization code from the user. To whitelist your endpoint, head to `https://discord.com/developers/applications/{YOUR APPLICATION ID}/oauth2/general` (if you don't have your application id at hand, go to `https://discord.com/developers/applications` and select your application, then click on OAuth2 in the left sidebar menu). Once there, under **Redirects**, hit the "Add another" button and enter `127.0.0.1:5000/auth` (if you have modified host, port or the endpoint name, adapt accordingly).


# Running these examples

### basic example
To run the basic example, you need to update the `CLIENT_ID` (line 17), `CLIENT_SECRET` (line 18) and `SESSION_SECRET` (line 19) variables with values for your app. If you haven't already stored them somewhere safe, you can retrieve them from your discord developers page. After that, run `main.py`. You will see some log output like the below:
```
INFO:     Started server process [XXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```
This means that the API is up and running. Now, navigate your web browser to http://127.0.0.1:5000/login. You will be redirected to a Discord authentication page. Log in if needed and then confirm your app's request to access your data. Upon confirming the request, you will be redirected once more and you'll see a json object containing your token similar to the one below:
```
{
  "access_token": "ACCESS TOKEN REDACTED",
  "expires_in": 604800,
  "refresh_token": "REFRESH TOKEN REDACTED",
  "scope": "identify",
  "token_type": "Bearer",
  "expires_at": 1651756835
}
```

### sessions example
To run the sessions example, you need to update the `CLIENT_ID`, `CLIENT_SECRET` and `SESSION_SECRET` (lines 22-24) variables with values for your app. After that, start the API as detailed in the basic example section. Don't head to http://127.0.0.1:5000/login straight away, however. First, visit http://127.0.0.1:5000/privileged. You'll be greeted with a "401 UNAUTHORIZED" error message because you need to be logged in to access this endpoint. Now, follow the same login process as the basic example. Instead of being displayed a token on success, you'll be redirected to `/users/me` and receive a JSON dump of your Discord information, including ID, name, discriminator and more. Also, if you inspect the cookies for your localhost, you will see that a session cookie has been set. This cookie contains an encoded version of the token from the basic example and is used by the `/users/me` endpoint to verify your identity and request your information from Discord. Finally, head to http://127.0.0.1:5000/privileged once more. Instead of the error, you will now see a message saying "Congratulations, you are logged in using Discord!".


# Extending these examples

### Using different authentication providers
The same ideas presented here can easily be applied to different remote identity providers, e.g. Google or Facebook, even in a single application. This can be done by registering another remote app in your code like so (change the scope according to what you need, I just grabbed a random one off of Google's OAuth2 tutorial website):
```python
oauth.register(
    'google',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    scope='https://www.googleapis.com/auth/drive.metadata.readonly',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET
)
```

The Google OAuth2 client defined in this manner would then be called with `oauth.google`, the rest of the flow doesn't need to change by much, though it is encouraged to build dedicated endpoints (`/login/discord`, `/login/google` and `/auth/discord`, `/auth/google`) for each identity provider (the main `/login` endpoint could list a choice of login options in this scenario). The token structure may differ from remote application to remote application, however. Make sure to account for that if you plan on using multiple identity providers. In that case, the `/auth` endpoint will have to do some user management, anyway (e.g. store the user, assign them a unique ID for your service and then store that in a user info cookie of some sort - see the comments in the auth endpoint of `sessions/main.py` on how to set custom cookies).

### Building your own permission system on top of the session infrastructure
By adding some user management to your `/auth` endpoint (i.e. storing the user ID in a database of some sort), you can build a custom permission system. This entails storing and managing a set of permissions along each user ID and building dependencies to ensure the user has the permissions needed to access a specific endpoint similar to `is_logged_in` in the `dependencies.py` file in the `sessions` example. Below, I'll give a brief, incomplete example to illustrate one way custom permission handling could be done:
```python
from fastapi import Depends, FastAPI, HTTPException, status
from starlette.requests import Request

# custom components
from dependencies import get_token


app = FastAPI()

async def get_user_id(request: Request):
    # ACTION ITEM: get the user ID from the request by means of extracting it from the "userinfo"
    # cookie (if implemented, see the comment in the auth endpoint of `sessions\main.py`
    # for details) or by querying the identity provider (Discord, in our example)
    import random
    user_id = random.choice([1234567890, None])

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )

    return user_id


class PermissionChecker:
    def __init__(self, permission):
        self.permission = permission

    def __call__(self, user_id=Depends(get_user_id)):
        # ACTION ITEM: query your database to see if the currently logged-in user
        # has self.permission
        import random
        has_permission = random.choice([True, False])
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient permissions'
            )

permission1 = 'Admin'  # this can be anything: strings, numeric IDs - design as you like
has_admin_permission = PermissionChecker(permission1)

permission2 = 'Something'
has_permission_two = PermissionChecker(permission2)

@app.get('/admin', dependencies=[Depends(has_admin_permission)])
async def admin_only():
    return 'You are an admin!'


@app.get('/privileged', dependencies=[Depends(has_permission_two)])
async def is_privileged():
    return 'You are truly privileged!'
```