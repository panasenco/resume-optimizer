const path = require("path");

module.exports = {
  entry: {
    popup: [
      "./popup.js",
      "./node_modules/@mozilla-protocol/core/protocol/css/protocol.css",
      "./node_modules/@mozilla-protocol/core/protocol/css/protocol-components.css",
    ],
    content: "./content-script.js",
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
    ]
  },
  mode: 'none',
};
