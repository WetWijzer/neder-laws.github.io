# Testing and Validation

WetWijzer has one active validation surface: the static Netherlands legal information site.

## Commands

```bash
npm install
npm run validate:netherlands-corpus
npm run build
npm test
npm run test:playwright
```

## Coverage

- `validate:netherlands-corpus` checks the browser-ready sample cache and confirms status metadata is present.
- `build` runs TypeScript and Vite production bundling.
- `test` runs Jest unit and logic tests.
- `test:playwright` runs browser smoke tests for WetWijzer branding, disclaimer, search, status display, and official source links.

WetWijzer is legal information, not legal advice. Tests verify software behavior only; they do not verify legal validity.
