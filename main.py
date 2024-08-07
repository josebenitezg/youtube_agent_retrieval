from fasthtml.common import *
from config import app
import views.chat_view  # This import is necessary to register the routes

# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
serve()