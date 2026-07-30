# Frontend Vite npm Windows Issues

## Symptoms

`npm run build` or `npm run test` can fail on Windows with one of these errors:

- `Error: spawn EPERM` while Vite or Vitest starts esbuild.
- `Failed to load PostCSS config` with `Unexpected token '﻿'` while parsing `package.json`.

## Causes

- PowerShell may block `npm.ps1`; use `npm.cmd` for local commands.
- The restricted sandbox can block esbuild binary spawn even after packages are installed.
- Windows PowerShell `Set-Content -Encoding UTF8` can write a UTF-8 BOM, and Vite's config search can reject a BOM-prefixed `package.json` as JSON.

## Fixes

- Run npm commands as `npm.cmd ...` in PowerShell.
- If esbuild install scripts were skipped or spawn is blocked, run `npm.cmd rebuild esbuild`; elevated execution may be required in restricted environments.
- Save `package.json` and config files as UTF-8 without BOM.
- Re-run `npm.cmd run lint`, `npm.cmd run test`, and `npm.cmd run build` after cleanup.
