import aiohttp
import uvicorn

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, FastAPI, status
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

# custom components
from dependencies import get_token, is_logged_in


# configuration parameters
HOST = '127.0.0.1'
PORT = 5000
DISCORD_API_PATH = 'https://discord.com/api/v9'

# in a productive app, DO NOT leave any of the following in your code
# ACTION ITEM: replace these placeholders with your own values
CLIENT_ID = 'YOUR CLIENT ID HERE'
CLIENT_SECRET = 'YOUR CLIENT SECRET HERE'
SESSION_SECRET = 'REPLACE WITH A PROPER SECRET OF YOUR CHOICE'


# initialize the API
app = FastAPI()


# add session middleware
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET,
                   max_age=60 * 60 * 24 * 7)  # one week, in seconds


# configure OAuth client
config = Config(environ={})  # you could also read the client ID and secret from a .env file
oauth = OAuth(config)
oauth.register(  # this allows us to call oauth.discord later on
    'discord',
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    scope='identify',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)


# define the endpoints for the OAuth2 flow
@app.get('/login')
async def get_authorization_code(request: Request):
    """OAuth2 flow, step 1: have the user log into Discord to obtain an authorization code grant
    """

    redirect_uri = request.url_for('auth')
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request):
    """OAuth2 flow, step 2: exchange the authorization code for access token
    """

    # exchange auth code for token
    try:
        token = await oauth.discord.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.error
        )

    # set the session cookie
    request.session['user'] = dict(token)

    # build the response
    response = RedirectResponse(url='/users/me')

    # you could also fetch additional user info here (see get_current_user) and set a
    # user info cookie like so (requires python-jose installed and "from jose import jwt"):
    # user_info = await get_current_user(token)
    # response.set_cookie('userinfo', jwt.encode(payload, SESSION_SECRET, algorithm='HS256'),
    #                     max_age=60 * 60 * 24 * 7)
    # this way, you'll always have user id, name etc. available from request.cookies['userinfo']
    # without needing to go and fetch it every time (you'll need to jwt.decode the cookie first)
    # Of course, the user info may be outdated this way, but you'll mainly need the static user id

    # redirect the user to the profile endpoint
    return response


# this endpoint is explicitly login-protected by requiring the token from the session cookie
@app.get('/users/me')
async def get_current_user(token=Depends(get_token)):
    """get the currently logged-in user based on their session cookie
    """

    # use the access token to fetch the user
    headers = {'Authorization': f'Bearer {token.get("access_token")}'}
    async with aiohttp.ClientSession() as sess:
        async with sess.get(DISCORD_API_PATH + '/users/@me', headers=headers) as response:
            # catch any http errors
            if response.status != status.HTTP_200_OK:
                response.raise_for_status()

            payload = await response.json()
    return payload


# this endpoint is implicitly login-protected via a dependency checking for a session cookie
@app.get('/privileged', dependencies=[Depends(is_logged_in)])
async def only_for_logged_in_users():
    return 'Congratulations, you are logged in using Discord!'


# run the API
if __name__ == '__main__':
    uvicorn.run('main:app', host=HOST, port=PORT)
