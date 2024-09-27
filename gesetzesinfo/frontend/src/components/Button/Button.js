import React from 'react';
import './Button.css';  // Import the CSS file

export function Button({
    text,
    onClick,
    baseColor = '#008CBA',
    textColor = '#fff',
    hoverColor = '#007bb5',
    activeColor = '#006b99'
}) {
    return (
        <div className="button-container">
            <button
                className="custom-button"
                onClick={onClick}
                style={{
                    '--base-color': baseColor,
                    '--text-color': textColor,
                    '--hover-color': hoverColor,
                    '--active-color': activeColor
                }}
            >
                {text}
            </button>
        </div>
    );
}
