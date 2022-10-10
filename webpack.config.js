const path = require("path");

module.exports = {
    entry: {
        background_scripts: "./background_scripts/background.js",
        popup: "./popup/left-pad.js",
        content: "./content-script.js"
    },
    output: {
        path: path.resolve(__dirname, "extension"),
        filename: "[name]/index.js"
    },
    mode: 'none',
};
