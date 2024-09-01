import React, { useState } from 'react';
import './ListItem.css';

function ListItem({ id, title, text }) {
    const [isExpanded, setIsExpanded] = useState(false);

    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
    };

    return (
        <div className={`list-item ${isExpanded ? 'expanded' : ''}`}>
            <div className={`list-item-header ${isExpanded ? 'expanded' : ''}`} onClick={toggleExpand}>
                <div className="list-item-id">{id}</div>
                <div className="list-item-title">{title}</div>
                <div className={`triangle `}></div>
            </div>
            <div className={`list-item-content ${isExpanded ? 'expanded' : ''}`}> 
                <div className='list-item-content-text'>{text}</div>
                <div className='list-item-interaction-bar'></div>
            </div>
        </div>
    );
}

export default ListItem;
