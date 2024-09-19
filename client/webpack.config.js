const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const STATIC = path.join(__dirname, 'static');
const SOURCE = path.join(__dirname, 'src');

module.exports = {
    mode: 'development',
    entry: './src/main.tsx',
    output: {
        path: STATIC,
        filename: 'bundle.js',
        clean: true,
        publicPath: '/',
    },
    devServer: {
        static: STATIC,
        hot: true,
        historyApiFallback: true,
    },
    devtool: 'inline-source-map',
    plugins: [
        new HtmlWebpackPlugin({
            template: path.join(SOURCE, 'index.html'),
        }),
    ],
    resolve: {
        extensions: ['.tsx', '.ts', '.jsx', '.js'],
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
            },
            {
                test: /\.jsx?$/,
                loader: 'babel-loader',
                options: {
                    presets: [
                        '@babel/preset-env',
                        '@babel/preset-react',
                        '@babel/preset-typescript',
                    ],
                },
            },
            {
                test: /\.css$/,
                use: [
                    {
                        loader: 'style-loader',
                    },
                    {
                        loader: 'css-loader',
                        options: {
                            modules: {
                                localIdentName: '[path][name]__[local]',
                            },
                        },
                    },
                ],
            },
            {
                test: /\.(png|svg|jpg|jpeg|gif)$/,
                type: 'asset/resource',
            },
        ],
    },
};
