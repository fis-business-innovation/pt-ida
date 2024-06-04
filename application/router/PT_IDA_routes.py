from fastapi import APIRouter, status, Header, Request
from application.core import PT_IDA_core

router = APIRouter(
    tags=['ML Model for IDA']
)

@router.post('/predict', status_code=status.HTTP_200_OK)
async def predict(request: Request, content_type: str = Header(), qualifier: str = Header(None, regex='^[A-Z]*$'), prefix: str = Header()):
    ''' Matching for IDA '''

    model_version = request.headers['model_version']
    if content_type == 'application/xml' or content_type == 'application/xml; charset=utf-8':
        body = await request.body()
        features = body.decode()

    if qualifier == '' or qualifier == ' ':
        qualifier = None

    prediction = PT_IDA_core.predict(
        features = features,
        qualifier = qualifier,
        prefix  = prefix, 
        model_version = model_version
    )

    return prediction
