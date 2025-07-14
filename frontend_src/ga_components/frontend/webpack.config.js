const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
  entry: "./src/index.tsx",
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  output: {
    filename: "main.js",
    path: path.resolve(__dirname, "build"),
    publicPath: "./"
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        loader: "ts-loader",
        exclude: /node_modules/
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      templateContent: `
        <!DOCTYPE html>
        <html>
          <head><meta charset="utf-8"><title>CPAoR Data Platform</title></head>
          <body><div id="root"></div></body>
        </html>
      `,
      inject: "body"
    })
  ]
};
