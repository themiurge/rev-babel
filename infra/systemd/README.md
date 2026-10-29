# systemd user units

`rev-babel-web.service` runs the web app on the teacher's desktop so it
survives reboots (linger must be enabled for the user). Install:

```sh
cp infra/systemd/rev-babel-web.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now rev-babel-web.service
```

Bind and port come from `.env` (`WEB_BIND`, `WEB_PORT`) via `scripts/run-web.sh`.
