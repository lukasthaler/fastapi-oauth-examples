# The OAuth2 authorization code flow using FastAPI
This repository showcases two examples of how to implement the OAuth2 authorization code flow and one example of the OAuth2 implicit grant flow.

The `basic` example contains the API routes needed to complete the OAuth2 authorization code flow. At the end, you'll be left with access and refresh tokens for the user and the scopes you requested.

The `sessions` example expands on that with signed session cookies managed by `starlette`'s `SessionMiddleware`. These session cookies allow a client to authenticate using a cookie issued to them by your API service. Since the cookies are *signed*, you'll be able to verify if they have been tampered with (actually, `starlette` automatically does that for you, denying modified cookies a session and thus, authentication). This example then also showcases how to get the currently active user and how to restrict endpoints to logged-in users only.

The `first_party` example implements the implicit grant flow. Please note that this flow is deprecated as of OAuth2.1. However, it is fine to implement this flow if you're going to be the only login authority, i.e. your users can only log in directly to your service, and you're not planning on using this as a third-party authorization provider for some other application. This example also showcases the use of API scopes to regulate access to endpoints.

**NOTE**: The examples showcased here are built as concise and straight-to-the point as possible, foregoing return models (using `pydantic`) and other advanced FastAPI features to put the spotlight on the OAuth2 flow. I will highlight some more advanced concepts in the **Extending these examples** section.


# Prerequisites
* These examples were built and tested using Python 3.9.13, but they should also work for lower versions provided the libraries are available.
* Install the dependencies listed in `requirements.txt`. The different examples each require a specific subset of the included libraries, see below for details. **All examples** need the following libraries to be installed: `fastapi` (for obvious reasons), `starlette` (this library will automatically be installed with `fastapi`, but I included it for clarity), `authlib` (to handle the OAuth2 flow), `httpx` and `itsdangerous` (required for `authlib ` to properly work), `uvicorn` (to serve the app). Additionally, the following libraries are necessary: 
  * `basic` example: no further libraries need to be installed
  * `sessions` example: `aiohttp` (asynchronous HTTP requests)
  * `first_party` example: `python-jose` (JWT (Json Web Token) handling to make access tokens work), `python-multipart` (required to receive user input from a web form)

  I chose to include running the app in the respective main files for ease of demonstration, but you'll probably want to run the app from the command line using some variation of `$ uvicorn main:app` in a productive environment.
* Your OAuth2 flow for the `basic` and `sessions` examples will be rejected unless you have authorized the redirect URI you request the flow to be directed to after obtaining the authorization code from the user. To whitelist your endpoint, head to `https://discord.com/developers/applications/{YOUR APPLICATION ID}/oauth2/general` (if you don't have your application id at hand, go to `https://discord.com/developers/applications` and select your application, then click on OAuth2 in the left sidebar menu). Once there, under **Redirects**, hit the "Add another" button and enter `127.0.0.1:5000/auth` (if you have modified host, port or the endpoint name, adapt accordingly).


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


### first party example
This example can be run as-is, no code modifications are required. Start the API by running `main.py`. To start off, head to http://127.0.0.1:5000/endpoint1 and http://127.0.0.1:5000/endpoint3. The first endpoint will greet you with a 401 Not Authorized error, the second will return a 200 response. If you have the ability to make HTTP requests (i.e. using a GUI like Postman or by using a command-line tool such as `curl`), please continue reading below. Otherwise, continue on to the "using the FastAPI swagger docs" section. 

##### using HTTP requests
Your next destination is http://127.0.0.1:5000/login. Provide any value for username and password, they are not validated in this example. For now, only check the first scope (`some.scope`) and leave the other two unchecked. Hit "Submit" and you'll be forwarded to http://127.0.0.1:5000/token and provided with an access token like the one below (if you're curious about the content of the token, you can decode it using a site like https://jwt.io):
```
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZXIiOiJteWFwcCIsInVzZXJuYW1lIjoiam9obmRvZSIsInNjb3BlcyI6InNvbWUuc2NvcGUiLCJleHBpcmVzX2F0IjoxNjcxNzI3NTY5Ljc3Mzc4Mn0.A9H--COsYLKJyp0Bf-lGQMEUganmyVYTDxjnYQOA68M",
  "token_type": "bearer"
}
```
Copy the access token. You now have access to endpoint 1, but not to endpoint 2. To verify this, hit both endpoints using an authorization header (`Authorization: Bearer TOKEN`, where `TOKEN` is the access_token string you received). The first will respond with "Hello from endpoint 1" and the second will hit you with a 403 Forbidden error message. That's it. You have your own implicit grant OAuth2 flow. If you want to try out different scope settings, just return to the login page and generate a new access token.

##### using the FastAPI swagger docs
Head to http://127.0.0.1:5000/docs and hit the green "Authorize" button in the top right of the page. Fill the `username` and `password` fields with arbitrary values (they are not validated) and enable `some.scope` by clicking the checkbox left of it. Leave everything else unchanged and click "Authorize" and then "Close". Next, go to `/endpoint1`, expand the section and hit "Try it out", then hit "Execute". You will receive a "Hello from endpoint 1" message. If you repeat the same process for `/endpoint2`, you will be greeted with a 403 Forbidden error message. That's it. You have your own implicit grant OAuth2 flow. If you want to try out different scope settings, just return to the login page and generate a new access token.


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