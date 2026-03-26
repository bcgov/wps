# WPS Web Monorepo

## Getting Started

### Dependencies

#### [Node.js](https://nodejs.org/en/)

You'll need Node 24.x and yarn. Use [nvm](https://github.com/nvm-sh/nvm#installation) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows#node-version-manager-nvm-for-windows) to switch Node versions between projects.

#### [yarn](https://yarnpkg.com/)

```
corepack enable
```

### Installing

All commands should be run from this directory (`web/`).

#### `yarn install`

Installs all dependencies for all packages in the monorepo.

## Executing

All of the following commands use [Turbo](https://turbo.build/) to orchestrate tasks across the monorepo. Create a `.env` file in `apps/wps-web/` using `apps/wps-web/.env.example` as a sample before running.

#### `yarn turbo dev`

Runs the app in development mode. The page will reload on edits and lint errors will appear in the console.

#### `yarn turbo test`

Launches the Vitest test runner across all packages, including unit tests and [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) component tests.

#### `yarn workspace @wps/wps-web run cy:open`

Launches the Cypress test runner in interactive watch mode for end-to-end and integration tests.

#### `yarn turbo build`

Builds the app for production to `apps/wps-web/build`.

##### Running in Docker

1. Create `.env` in `apps/wps-web/` using `apps/wps-web/.env.example` as a sample
2. Run `docker compose build` and then `docker compose up`
3. Open [http://localhost:3000](http://localhost:3000)

## Structure

```
apps/
  wps-web/        # Main React app (@wps/wps-web)
packages/
  api/            # API client functions (@wps/api)
  types/          # Shared type declarations (@wps/types)
  ui/             # Shared React components (@wps/ui)
  utils/          # Shared utilities (@wps/utils)
  tsconfig/       # Shared TypeScript configs (@wps/tsconfig)
```

## Dependency Management

Each package declares its own dependencies explicitly in its `package.json`. This matters because multiple apps consume these packages — a new app that omits a dependency that happens to be hoisted by another package will fail in non-obvious ways.

### Rules

- Runtime imports → `dependencies`
- `import type` only → `devDependencies`
- Workspace packages used only for types → `devDependencies` (e.g. `@wps/types`)

### Why builds don't currently fail on undeclared deps

The workspace uses `nodeLinker: node-modules` (configured in `.yarnrc.yml`), which hoists all packages into a shared `node_modules`. Any package can resolve any other package at build time regardless of what's declared.

### Enforcing strict dependency boundaries (future)

Switching to `nodeLinker: pnp` (Yarn Plug'n'Play) would enforce strict boundaries — packages can only import what they explicitly declare, and build errors surface immediately. PnP also reduces disk usage and speeds up installs by storing packages as zips rather than extracted file trees. This hasn't been adopted yet due to migration risk (Vite and other tooling require PnP compatibility verification).
