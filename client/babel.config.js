module.exports = {
  "presets": [
    [
      "@babel/preset-env",
      {
        "targets": {
          "edge": "17",
          "firefox": "60",
          "chrome": "67",
          "safari": "11.1"
        },
        "useBuiltIns": "usage",
        "corejs": "3.6.5"
      },
    ],
    [
      "@babel/preset-typescript",
      {
          "allExtensions": true,
          "isTSX": true
      },
    ],
    [
      "@babel/preset-react",
      {
          "development": process.env.NODE_ENV === "development",
      }
    ]
  ]
}
