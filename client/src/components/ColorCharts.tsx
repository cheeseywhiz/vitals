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

type Channel = "red" | "green" | "blue";

type RgbColor = {
    red: number;
    green: number;
    blue: number;
};

function RgbToHex({ red, green, blue }: RgbColor): string {
    return "#" + ChannelToHex(red) + ChannelToHex(green) + ChannelToHex(blue);
}

function ChannelToHex(value: number) {
    if (value > 255) value = 255;
    let hex = value.toString(16);
    if (hex.length < 2) hex = "0" + hex;
    return hex;
}

function Range(start: number, stop: number, nSteps: number): number[] {
    const sign = Math.abs(stop - start) / (stop - start);
    const dx = (stop - start + sign) / nSteps;
    const length = Math.abs(Math.ceil((stop - start) / dx));
    const numbers = Array.from({ length }).fill(start) as number[];
    return [...numbers.map((x, y) => x + y * dx), stop];
}

// only one number is provided, that is the shade of the chart.
// the other two form the axes of the chart.
type ChartProps = {
    red?: number;
    green?: number;
    blue?: number;

    setChannel: (channel: number) => void;
};

function Chart({ red, green, blue, setChannel }: ChartProps) {
    const nSteps = 16;
    const cellWidth = "24px";
    const chartHeight = "500px";
    let shade: Channel;
    let shadeValue: number;
    let xAxis: Channel;
    let yAxis: Channel;

    if (red !== undefined) {
        shade = "red";
        shadeValue = red;
        xAxis = "blue";
        yAxis = "green";
    } else if (green != undefined) {
        shade = "green";
        shadeValue = green;
        xAxis = "red";
        yAxis = "blue";
    } else if (blue != undefined) {
        shade = "blue";
        shadeValue = blue;
        xAxis = "green";
        yAxis = "red";
    } else {
        return <p>Chart props error</p>
    }

    return <>
        <p>{shade}: {shadeValue}</p>
        <input
            type="range"
            min="0"
            max="255"
            step={1}
            value={shadeValue} style={{ width: "100%" }}
            onChange={(e) => setChannel(parseFloat(e.target.value))}
        />
        <p>x axis: {xAxis}</p>
        <p>y axis: {yAxis}</p>
        <div style={{
            display: "flex",
            flexDirection: "column",
            width: "100%",
            height: chartHeight,
        }}>
            {Range(255, 0, nSteps).map(yValue => (
                <div key={yValue} style={{
                    display: "flex",
                    width: "100%",
                    height: cellWidth,
                }}>
                    {Range(0, 255, nSteps).map(xValue => {
                        const rgbColor: RgbColor = {
                            red, green, blue,
                            [shade]: shadeValue,
                            [xAxis]: xValue,
                            [yAxis]: yValue,
                        };
                        const rgbHex = RgbToHex(rgbColor);
                        return <Fragment key={xValue}>
                            <Swatch style={{flex: 1}} width={cellWidth} color={rgbHex} />
                        </Fragment>
                    })}
                </div>
            ))}
        </div>
    </>;
}

export default function ColorCharts() {
    const [ red, setRed ] = useState<number>(128);
    const [ green, setGreen ] = useState<number>(128);
    const [ blue, setBlue ] = useState<number>(128);
    const rgbColor: RgbColor = {
        red, green, blue,
    };
    const rgbHex = RgbToHex(rgbColor);

    return <div style={{ width: "40%" }}>
        <Swatch color={rgbHex} height={100} width={100} />
        <Chart red={red} setChannel={setRed} />
        <Chart green={green} setChannel={setGreen} />
        <Chart blue={blue} setChannel={setBlue} />
    </div>;
}
