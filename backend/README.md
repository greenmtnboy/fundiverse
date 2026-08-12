## Backend Script

Must be compiled with pyinstaller and copied into the frontend executable folder.

This will be done in CI automatically or by the frontend build script.

## Installing dependencies

```
pip install -r requirements.txt
pip install --no-deps -r requirements-webull.txt
```

The second line is required: Webull's official SDK declares streaming
sub-packages that pin dependencies with no Python 3.12+ wheels. See the
comments in `requirements-webull.txt`. Without it the Webull provider is simply
absent from `/providers` rather than erroring.

## Building

Debug:
pyinstaller main.py  --noconsole  --name py-portfolio-ui-backend  --hidden-import py-portfolio-index  --collect-all py_portfolio_index --hidden-import alpaca-py --collect-all uvicorn --noconfirm --clean --additional-hooks-dir extra-hooks

Release:
 pyinstaller main.py  --noconsole --onefile --name py-portfolio-ui-backend --hidden-import py-portfolio-index --collect-all py_portfolio_index  --hidden-import alpaca-py --collect-all uvicorn --noconfirm --clean --additional-hooks-dir extra-hooks


 ## WSL Specifics

 Can install local copy of py-portfolio-index by using WSL access

 `pip install /mnt/c/users/[user]/coding_projects/py-portfolio-index`