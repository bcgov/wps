""" Pydantic schemas for the SFMS API. """
from pydantic import BaseModel


class ProcessRequest(BaseModel):
    """ The process request must contain a secret that matches expectation """
    secret: str
