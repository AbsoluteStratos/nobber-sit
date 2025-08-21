# Nobber Sit

Emote statistic tracking

## Front End Developers

Created from:

```sh
npm create astro@latest -- --template basics
```
### 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |


### Automation

For the Github Workflow automation there are three items needed:

- `GH_PAT`: Github personal access token for this repo scope, with contents (read and write) permissions. This is needed so the update commits from the workflow will trigger the gh-pages
pipelines.
- `TWITCH_API_CLIENT_ID`: API client ID gotten from registering a [twitch app to the API](https://dev.twitch.tv/console/apps)
- `TWITCH_API_CLIENT_SECRET`: API client ID gotten from registering a [twitch app to the API](https://dev.twitch.tv/console/apps)

> For the twitch app, the oauth url can be `https://localhost`
