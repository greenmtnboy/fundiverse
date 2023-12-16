## Backend Script

Must be compiled with pyinstaller and copied into the frontend executable folder.

This will be done in CI automatically or by the frontend build script.

## Building

Debug:
pyinstaller main.py  --noconsole  --name py-portfolio-ui-backend  --hidden-import py-portfolio-index  --collect-all py_portfolio_index --hidden-import alpaca-py --collect-all uvicorn --noconfirm --clean --additional-hooks-dir extra-hooks

Release:
 pyinstaller main.py  --noconsole --onefile --name py-portfolio-ui-backend --hidden-import py-portfolio-index --collect-all py_portfolio_index  --hidden-import alpaca-py --collect-all uvicorn --noconfirm --clean --additional-hooks-dir extra-hooks


 ## WSL Specifics

 Can install local copy of py-portfolio-index by using WSL access

 `pip install /mnt/c/users/[user]/coding_projects/py-portfolio-index`