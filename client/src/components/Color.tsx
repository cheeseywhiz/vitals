import React, { useState, Fragment } from 'react';

type SwatchProps = {
    color: string;
    height?: number;
    width?: number | string;
    style?: any;
};

function Swatch({ color, height, width, style }: SwatchProps) {
    if (width === undefined) width = "stretch";
    if (height === undefined) height = 100;
    return <>
        <div style={{
            height,
            width,
            background: color,
            ...style
        }}>
        </div>
    </>;
    /*
            {color}
     */
    return <p>Color: {color}</p>;
}

type Channel = "cyan" | "magenta" | "yellow" | "key";

type CmykColor = {
    cyan: number;
    magenta: number;
    yellow: number;
    key: number;
};

function CmykToRgb({ cyan, magenta, yellow, key }: CmykColor) {
    const red = convertChannel(cyan, key);
    const green = convertChannel(magenta, key);
    const blue = convertChannel(yellow, key);
    return "#" + red + green + blue;
}

function convertChannel(value: number, key: number) {
    let num = Math.floor(255 * (1 - value) * (1 - key));
    if (num > 255) num = 255;
    let hex = num.toString(16);
    if (hex.length < 2) hex = "0" + hex;
    return hex;
}

type PaletteProps = {
    color: CmykColor;
    channel: Channel;
    setChannel: (channel: number) => void;
};

function Palette({ color, channel, setChannel }: PaletteProps) {
    const nSteps = 256;
    return <div>
        <p>{channel}: {color[channel]}</p>
        <input
            type="range"
            min="0"
            max="1"
            step={1 / 256}
            value={color[channel]} style={{ width: "100%" }}
            onChange={(e) => setChannel(parseFloat(e.target.value))}
        />
        <div style={{
            display: "flex",
            width: "100%",
        }}>
            {Range(0, 1, nSteps).map(num => {
                const newCmykColor = { ...color, [channel]: num };
                const rgbColor = CmykToRgb(newCmykColor);
                return <Fragment key={num}>
                    <Swatch style={{flex: 1}} color={rgbColor} />
                </Fragment>;
            })}
        </div>
    </div>
}

function Range(start: number, stop: number, nSteps: number): number[] {
    const dx = (stop - start) / nSteps;
    const length = Math.ceil((stop - start) / dx);
    const numbers = Array.from({ length }).fill(start) as number[];
    return [...numbers.map((x, y) => x + y * dx), stop];
}

export default function Color() {
    const [ cyan, setCyan ] = useState<number>(0);
    const [ magenta, setMagenta ] = useState<number>(0.5);
    const [ yellow, setYellow ] = useState<number>(1);
    const [ key, setKey ] = useState<number>(0);
    const cmykColor: CmykColor = { cyan, magenta, yellow, key };
    const rgbColor = CmykToRgb(cmykColor);

    return <div style={{ width: "40%" }}>
        <Swatch color={rgbColor} height={100} width={100} />
        <Palette color={cmykColor} channel="cyan" setChannel={setCyan} />
        <Palette color={cmykColor} channel="magenta" setChannel={setMagenta} />
        <Palette color={cmykColor} channel="yellow" setChannel={setYellow} />
        <Palette color={cmykColor} channel="key" setChannel={setKey} />
    </div>;
}
