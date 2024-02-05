## Static Site Generation

Docs are built with vuepress.

### Deployment

Docs are served via a static website provider.


Build, then copy files

`npm run build`

Optionally, if copying off WSL

`sudo npm run build && cp -r src/.vuepress/dist /mnt/c/Users/ethan/docs_dist`

Suggest using filezilla to copy.
