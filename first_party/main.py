import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Security, status
from starlette.responses import HTMLResponse

# custom components
from security import APP_NAME, create_access_token, ensure_permissions, OAuth2Form, SCOPES, validate_login


# configuration parameters
HOST = '127.0.0.1'
PORT = 5000


# initialize the API
app = FastAPI()


# define the endpoints for the OAuth2 flow

@app.get('/login')
async def login_page():
    """OAuth2 implicit flow, step 1.1: have the user log in and confirm a set of scopes
    """

    # build and send a basic login page
    html_header = '''
        <form method="POST" action="/token">
            <label for="username">Username:</label>
            <input id="username" type="text" name="username"/><br/>
            <label for="password">Password:</label>
            <input id="password" type="password" name="password"/><br/>
    '''

    if SCOPES:
        scope_template = '''
            <input id="{scope}" type="checkbox" name="scope" value="{scope}" checked/>
            <label for="{scope}">{scope}</label><br/>
        '''
        html_scopes = ''.join(scope_template.format(scope=scope) for scope in SCOPES)
    else:
        html_scopes = ''

    html_footer = '''
            <input type="submit" value="Submit"/>
        </form>
    '''

    return HTMLResponse(html_header + html_scopes + html_footer)


@app.post('/token')
async def login_for_token(form_data: OAuth2Form = Depends()):
    """OAuth2 password bearer flow: exchange username/password for access token
    """

    # validate username/password
    if not validate_login(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )

    # generate access token
    # NOTE: in a productive environment, you have to validate the requested scopes against the user's permissions
    # otherwise, attackers may be able to get more permissions than they are supposed to have
    token_data = {'issuer': APP_NAME, 'username': form_data.username, 'scopes': ' '.join(form_data.scopes)}
    access_token = create_access_token(token_data)

    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get('/endpoint1', dependencies=[Security(ensure_permissions, scopes=['some.scope', 'third.scope'])])
def endpoint1():
    return 'Hello from endpoint 1'


@app.get('/endpoint2', dependencies=[Security(ensure_permissions, scopes=['other.scope', 'third.scope'])])
def endpoint2():
    return 'Hello from endpoint 2'


@app.get('/endpoint3')
def endpoint3():
    return 'Hello from the unprotected endpoint 3'


# run the API
if __name__ == '__main__':
    uvicorn.run('main:app', host=HOST, port=PORT)
