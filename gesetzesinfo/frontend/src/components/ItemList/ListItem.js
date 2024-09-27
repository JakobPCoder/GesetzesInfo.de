import React, { useState } from 'react';
import './ListItem.css';
import { Button } from '../Button/Button';



function ListItem({ id, title, text, query, score }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [queryText, setQueryText] = useState(query);

    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
    };


    const handleRatingClick = (positive) => {
        const query = `http://${encodeURIComponent(process.env.API_DOMAIN || "localhost")}:${encodeURIComponent(process.env.BACKEND_PORT || 8000)}/api/rate_results?p=${encodeURIComponent(positive)}&q=${encodeURIComponent(queryText)}&id=${encodeURIComponent(id)}`;

        fetch(query)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        });
    };

    const handleContentClick = (event) => {
        // Check if the click is not on the interaction bar
        if (!event.target.closest('.list-item-interaction-bar')) {
            toggleExpand();
        }
    };
    
    function InteractionBar() {
        return (
            <div className="list-item-interaction-bar">
                {/* <Button text="This was helpful" onClick={handleRatingClick(true)} />
                <Button text="Unrelated" onClick={handleRatingClick(false)} /> */}
                <Button text="This was helpful" baseColor="var(--color-rating-positive)"/>
                <Button text="Unrelated" baseColor="var(--color-rating-negative)"/>
            </div>
        );
    }
    

    return (
        <div className={`list-item ${isExpanded ? 'expanded' : ''}`} onClick={handleContentClick}>
            <div className="list-item-header">
                <div className="list-item-id">{id}</div>
                <div className="list-item-title">{title}</div>
                <div className="list-item-score">{score ? score.toFixed(4) : '0.00'}</div>
                <div className="triangle"></div>
            </div>
            <div className="list-item-content">
                <div className="list-item-content-text">{text}</div>
                <InteractionBar />
            </div>
        </div>
    );
}

export default ListItem;
