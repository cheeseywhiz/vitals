import React from 'react';
import { createPortal } from 'react-dom';

type DialogProps = {
    prompt: string;
    onYes?: () => void;
    onNo?: () => void;
};

export default function Dialog({ prompt, onYes, onNo }: DialogProps) {
    return createPortal(
        <ul>
            <li>{prompt}</li>
            <ul>
                <li><button onClick={onYes}>Yes</button></li>
                <li><button onClick={onNo}>No</button></li>
            </ul>
        </ul>,
        document.getElementById('vitals-react-app')
    );
}
