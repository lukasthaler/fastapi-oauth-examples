import uvicorn

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, HTTPException, status
from starlette.config import Config
from starlette.requests import Request


# configuration parameters
HOST = '127.0.0.1'
PORT = 5000
SCOPE = 'identify'  # if you need more scopes, add them to the string (separated with whitespaces)

# in a productive app, DO NOT leave any of the following in your code
# ACTION ITEM: replace these placeholders with your own values
CLIENT_ID = 'YOUR CLIENT ID HERE'
CLIENT_SECRET = 'YOUR CLIENT SECRET HERE'


# initialize the API
app = FastAPI()


# configure OAuth client
config = Config(environ={})  # you could also read the client ID and secret from a .env file
oauth = OAuth(config)
oauth.register(  # this allows us to call oauth.discord later on
    'discord',
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    scope=SCOPE,
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

    # you now have a Discord token. Do whatever you need with it
    return token


# run the API
if __name__ == '__main__':
    uvicorn.run('main:app', host=HOST, port=PORT)
