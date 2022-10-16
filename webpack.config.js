const path = require("path");

module.exports = {
  entry: {
    background: "./background-script.js",
    content: "./content-script.js",
    popup: [
      "./popup.js",
      "./node_modules/@mozilla-protocol/core/protocol/css/protocol.css",
      "./node_modules/@mozilla-protocol/core/protocol/css/protocol-components.css",
    ],
  },
  output: {
    path: path.resolve(__dirname, "extension"),
    filename: "[name]/index.js"
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        type: "asset/resource",
        generator: {
          filename: "popup/[name].css",
        },
      },
      {
        test: /\.ambiguity$/,
        type: "asset/source",
        generator: {
          filename: "background/[name].ambiguity",
        },
      },
    ]
  },
  mode: 'none',
};
