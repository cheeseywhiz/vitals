import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";


export default [
    {
        files: [
            "src/**/*.{js,mjs,cjs,ts,jsx,tsx}",
        ],
    },
    {
        ignores: [
            "*.{js,mjs,cjs,ts,jsx,tsx}",
            "static/**/*.js",
        ],
    },
    {languageOptions: { globals: globals.browser }},
    pluginJs.configs.recommended,
    ...tseslint.configs.recommended,
    pluginReact.configs.flat.recommended,
    {
        settings: {
            react: {
                version: 'detect',
            },
        },
    },
    {
        "rules": {
            // https://stackoverflow.com/a/64067915
            "no-unused-vars": "off",
            "@typescript-eslint/no-unused-vars": [
                "warn",
                {
                    "argsIgnorePattern": "^_",
                    "varsIgnorePattern": "^_",
                    "caughtErrorsIgnorePattern": "^_",
                },
            ],
        },
    },
];
