from fastapi import HTTPException, status
from starlette.requests import Request


def get_token(request: Request):
    """a dependency to extract the token from the request's session cookie
    """

    session = request.session
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    return session['user']


async def is_logged_in(request: Request):
    """a dependency to ensure a user is logged in via a session cookie
    """

    session = request.session
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
